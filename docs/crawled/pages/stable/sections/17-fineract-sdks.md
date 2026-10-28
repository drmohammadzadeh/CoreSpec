---
source_url: https://fineract.apache.org/docs/1.16.0#_fineract_sdks
title: "Fineract SDKs"
depth: 1
crawled_at: 2026-10-28T13:56:51.858405+00:00
parent_url: https://fineract.apache.org/docs/stable
---

## Fineract SDKs

TBD

### Generate Apache Fineract API Client

Apache Fineract supports client code generation using [OpenAPI Generator](https://openapi-generator.tech). It uses [OpenAPI Specification Version 3.0.3](https://swagger.io/specification/).

#### Fineract SDK Java API Client

The `fineract-client.jar` will eventually be available on Maven Central (watch [FINERACT-1102](https://issues.apache.org/jira/browse/FINERACT-1102)). Until it is, you can quite easily build the latest and greatest version locally from source, see below.

The [`FineractClient`](https://github.com/search?q=repo%3Aapache%2Ffineract+path%3AFineractClient.java&type=code) is the entry point to the *Fineract SDK Java API Client*. [`Calls`](https://github.com/search?l=&q=repo%3Aapache%2Ffineract+path%3ACalls.java&type=code) is a convenient and recommended utility to simplify the use of the [`retrofit2.Call`](https://square.github.io/retrofit/2.x/retrofit/retrofit2/Call.html) type which all API operations return. This permits you to use the API like the [`FineractClientDemo`](https://github.com/search?l=&q=repo%3Aapache%2Ffineract+path%3AFineractClientDemo.java&type=code) illustrates:

```java
import org.apache.fineract.client.util.FineractClient;
import static org.apache.fineract.client.util.Calls.ok;

        FineractClient fineract = FineractClient.builder().baseURL("https://demo.fineract.dev/fineract-provider/api/v1/").tenant("default")
                .basicAuth("mifos", "password").build();
        List<StaffData> staff = Calls.ok(fineract.staff.retrieveAllStaff(1L, true, false, "ACTIVE"));
        String name = staff.get(0).getDisplayName();
        log.info("Display name: {}", name);
```

#### Generate API Client

The API client is built as part of the standard overall Fineract Gradle build. The client JAR can be found in `fineract-client/build/libs` as `fineract-client.jar`.

If you need to save time to incrementally work on making small changes to Swagger annotations in an IDE, you can execute e.g. the following line in root directory of the project to exclude non-require Gradle tasks:

```java
./gradlew -x compileJava -x compileTest -x spotlessJava -x enhance resolve prepareInputYaml :fineract-client:buildJavaSdk
```

#### Validate OpenAPI Spec File

The `resolve` task in [build.gradle](https://github.com/apache/fineract/blob/develop/fineract-provider/build.gradle#L80) file will generate the OpenAPI Spec File for the project. To make sure Swagger Codegen generates a correct library, it is important for the OpenAPI Spec file to be valid. Validation is done automatically by the OpenAPI code generator Gradle plugin. If you still have problems during code generation please use [Swagger OpenAPI Validator](https://validator.swagger.io/) to validate the spec file.