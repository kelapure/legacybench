# Sandbox image for Java 8 -> 17 migration tasks.
# Build with scripts/build_image.sh, which first clones every manifest repo at its
# pinned commit into docker/repos/<id>/ so this build can warm the offline Maven
# repository. At run time the container has no network (compose.yaml).
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
      openjdk-8-jdk-headless openjdk-17-jdk-headless maven git ca-certificates coreutils findutils \
    && rm -rf /var/lib/apt/lists/*

ENV JAVA8_HOME=/usr/lib/jvm/java-8-openjdk-amd64
ENV JAVA17_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV MAVEN_OPTS="-Dmaven.repo.local=/opt/m2"

RUN useradd -m -s /bin/bash agent && mkdir -p /workspace /opt/m2 && chown agent:agent /workspace /opt/m2

# Reference copies of the task repositories, read-only to the agent.
COPY repos/ /opt/repos/

# Warm the offline Maven cache for every repo on both JDKs, plus JaCoCo.
# Failures here are tolerated per repo so one broken pom does not block the image;
# the scorer will report such repos as build failures and they must be excluded
# from the manifest before pre-registration.
RUN set -e; for d in /opt/repos/*/; do \
      ( cd "$d" && JAVA_HOME=$JAVA8_HOME mvn -B -q dependency:go-offline -Dmaven.repo.local=/opt/m2 || true ); \
      ( cd "$d" && JAVA_HOME=$JAVA17_HOME mvn -B -q dependency:go-offline -Dmaven.repo.local=/opt/m2 || true ); \
      ( cd "$d" && JAVA_HOME=$JAVA17_HOME mvn -B -q org.jacoco:jacoco-maven-plugin:0.8.12:help -Dmaven.repo.local=/opt/m2 || true ); \
    done; chmod -R a-w /opt/repos; chown -R agent:agent /opt/m2

USER root
WORKDIR /workspace
CMD ["tail", "-f", "/dev/null"]
