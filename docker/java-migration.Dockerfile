# Sandbox image for Java 8 -> 17 migration tasks.
# Build with scripts/build_image.sh, which first clones every manifest repo at its
# pinned commit into docker/repos/<id>/ so this build can warm the offline Maven
# repository. At run time the container has no network (compose.yaml).
#
# Works on amd64 and arm64 (Apple Silicon): JDK paths are resolved to /opt/jdk8 and
# /opt/jdk17 symlinks at build time.
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
      openjdk-8-jdk-headless openjdk-17-jdk-headless maven git ca-certificates \
      coreutils findutils pipx python3 \
    && rm -rf /var/lib/apt/lists/* \
    && ln -s "$(ls -d /usr/lib/jvm/java-8-openjdk-* | head -n1)" /opt/jdk8 \
    && ln -s "$(ls -d /usr/lib/jvm/java-17-openjdk-* | head -n1)" /opt/jdk17

ENV JAVA8_HOME=/opt/jdk8
ENV JAVA17_HOME=/opt/jdk17
ENV JAVA_HOME=/opt/jdk17
ENV MAVEN_OPTS="-Dmaven.repo.local=/opt/m2"

# Inspect's text_editor tool needs inspect-tool-support inside the sandbox
# (bash does not). Installed system-wide so the non-root agent user can use it.
ENV PATH="$PATH:/opt/inspect/bin"
RUN PIPX_HOME=/opt/inspect/pipx PIPX_BIN_DIR=/opt/inspect/bin PIPX_VENV_DIR=/opt/inspect/pipx/venvs \
      pipx install inspect-tool-support && chmod -R 755 /opt/inspect && inspect-tool-support post-install

RUN useradd -m -s /bin/bash agent && mkdir -p /workspace /opt/m2 /opt/baselines && chown agent:agent /workspace /opt/m2

# Reference copies of the task repositories, read-only to the agent.
COPY repos/ /opt/repos/

# Warm the offline Maven cache. `dependency:go-offline` misses Surefire's per-framework
# provider jars and the JaCoCo agent, which Maven resolves lazily at test time, so each
# repo's tests are run once on JDK 8 with JaCoCo. That also records the baseline test
# log in /opt/baselines/<id>.log (used by scripts/verify_image.py). Per-repo failures
# are tolerated here and surfaced by verify_image.py; a repo that does not pass on JDK 8
# must be dropped from the manifest before pre-registration.
RUN set -e; for d in /opt/repos/*/; do id="$(basename "$d")"; \
      ( cd "$d" && JAVA_HOME=$JAVA8_HOME mvn -B -q dependency:go-offline -Dmaven.repo.local=/opt/m2 || true ); \
      ( cd "$d" && JAVA_HOME=$JAVA8_HOME mvn -B org.jacoco:jacoco-maven-plugin:0.8.12:prepare-agent test org.jacoco:jacoco-maven-plugin:0.8.12:report -Dmaven.repo.local=/opt/m2 > "/opt/baselines/$id.log" 2>&1 || true ); \
      ( cd "$d" && JAVA_HOME=$JAVA17_HOME mvn -B -q dependency:go-offline -Dmaven.repo.local=/opt/m2 || true ); \
      ( cd "$d" && JAVA_HOME=$JAVA17_HOME mvn -B -q test-compile -Dmaven.repo.local=/opt/m2 || true ); \
      ( cd "$d" && mvn -B -q clean -Dmaven.repo.local=/opt/m2 || true ); \
    done; chmod -R a-w /opt/repos; chown -R agent:agent /opt/m2

USER root
WORKDIR /workspace
CMD ["tail", "-f", "/dev/null"]
