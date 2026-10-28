---
source_url: https://fineract.apache.org/docs/1.16.0#_fineract_development_environment
title: "Fineract Development Environment"
depth: 1
crawled_at: 2026-10-28T13:56:51.858405+00:00
parent_url: https://fineract.apache.org/docs/stable
---

## Fineract Development Environment

* 16GB RAM and 8 core CPU (minimum hardware for running Fineract — development and testing may require more)
* PostgreSQL >= 18.0 ([support for other backend databases is deprecated](https://cwiki.apache.org/confluence/display/FINERACT/FSIP-9%3A+Standardize+on+PostgreSQL))
* Java >= 25 ([Azul Zulu JVM](https://www.azul.com/downloads/?package=jdk#zulu) is tested by our CI on GitHub Actions)

Tomcat (min. v10) is only needed if you wish to deploy the Fineract WAR to a separate external servlet container. You do not need to install Tomcat to run Fineract. We recommend the use of the self-contained JAR, which transparently embeds a servlet container using Spring Boot.

### Git

Version 2.23 or later (supporting `git switch` and `git restore`).

### GnuPG

GNU Privacy Guard is used for signing commits and releases and for verifying those signatures. Any [non-EOL v2 release of GnuPG](https://gnupg.org/download/#end-of-life) should work.

See Signing releases for help generating keys.

#### Committers

Provide your public key fingerprint in your Apache committer profile at [id.apache.org](https://id.apache.org).

#### PMC members

Include your public key in [our KEYS file](https://downloads.apache.org/fineract/KEYS).

### Docker

TBD

#### Docker Compose

TBD

#### Podman

TBD

#### Rancher Docker Desktop

TBD

### Gradle

The [Gradle Wrapper](https://docs.gradle.org/current/userguide/gradle_wrapper.html) included with Fineract will automatically run the correct version of Gradle.

### IDE

TBD

#### IntelliJ

TBD

#### Eclipse

TBD

#### VSCode

TBD

### Kubernetes

TBD

#### Minikube

TBD

#### Microk8s

TBD

#### K3d

TBD

#### Helm Charts

TBD

### Tools

TBD

#### SDKMAN

We recommend using SDKMAN to manage the following developer tools:

* JDK
* Spring Boot CLI
* Gradle (if you need a global installation)
* AsciidoctorJ

TBD

#### Brew

##### MacOS

TBD

##### Linux

TBD