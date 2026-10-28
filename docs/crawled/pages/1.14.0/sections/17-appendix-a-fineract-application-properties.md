---
source_url: https://fineract.apache.org/docs/1.14.0#_fineract_application_properties
title: "Appendix A: Fineract Application Properties"
depth: 2
crawled_at: 2026-10-28T13:56:51.858405+00:00
parent_url: https://fineract.apache.org/docs/1.14.0
---

## Appendix A: Fineract Application Properties

TBD

### Tenant Database Properties

| Name | Env Variable | Default Value | Description |
| --- | --- | --- | --- |
| fineract.tenant.host | FINERACT_DEFAULT_TENANTDB_HOSTNAME | localhost | This property sets the hostname of the default tenant database. |
| fineract.tenant.port | FINERACT_DEFAULT_TENANTDB_PORT | 3306 | This property sets the port of the default tenant database. |
| fineract.tenant.username | FINERACT_DEFAULT_TENANTDB_UID | root | This property sets the username of the default tenant database. |
| fineract.tenant.password | FINERACT_DEFAULT_TENANTDB_PWD | mysql | This property sets the password of the default tenant database. |
| fineract.tenant.parameters | FINERACT_DEFAULT_TENANTDB_CONN_PARAMS |  | This property sets the connection parameters of the default tenant database. eg. whether ssl is enabled or not |
| fineract.tenant.timezone | FINERACT_DEFAULT_TENANTDB_TIMEZONE | Asia/Kolkata | This property sets the timezone of the default tenant |
| fineract.tenant.identifier | FINERACT_DEFAULT_TENANTDB_IDENTIFIER | default | This property sets the unique identifier for the tenant within fineract |
| fineract.tenant.name | FINERACT_DEFAULT_TENANTDB_NAME | fineract_default | This property sets the database name of the default tenant |
| fineract.tenant.description | FINERACT_DEFAULT_TENANTDB_DESCRIPTION | Default Demo Tenant | This property sets the description of the default tenant |
| fineract.tenant.master-password | FINERACT_DEFAULT_TENANTDB_MASTER_PASSWORD | fineract | The password used to encrypt sensitive tenant data within the database |
| fineract.tenant.encryption | FINERACT_DEFAULT_TENANTDB_ENCRYPTION | AES/CBC/PKCS5Padding | This property sets the symmetric encryption algorithm used to encrypt sensitive tenant data within the database e.g tenant database password |
| spring.liquibase.enabled | FINERACT_LIQUIBASE_ENABLED | true | If set to true, liquibase will be enabled and the instance running this configuration will run migrations |
| fineract.tenant.read-only-name | FINERACT_DEFAULT_TENANTDB_RO_NAME |  | For read only configuration, set this to the name of the read only tenant database |
| fineract.tenant.read-only-host | FINERACT_DEFAULT_TENANTDB_RO_HOSTNAME |  | For read only configuration, set this to the hostname of the read only tenant database |
| fineract.tenant.read-only-port | FINERACT_DEFAULT_TENANTDB_RO_PORT |  | For read only configuration, set this to the port of the read only tenant database |
| fineract.tenant.read-only-username | FINERACT_DEFAULT_TENANTDB_RO_UID |  | For read only configuration, set this to the username of the read only tenant database |
| fineract.tenant.read-only-password | FINERACT_DEFAULT_TENANTDB_RO_PWD |  | For read only configuration, set this to the password of the read only tenant database |
| fineract.tenant.read-only-parameters | FINERACT_DEFAULT_TENANTDB_RO_CONN_PARAMS |  | For read only configuration, set this to the connection parameters of the read only tenant database |

### Hikari Connection Pool Properties

| Name | Env Variable | Default Value | Description |
| --- | --- | --- | --- |
| spring.datasource.hikari.driverClassName | FINERACT_HIKARI_DRIVER_SOURCE_CLASS_NAME | org.mariadb.jdbc.Driver | The correct driver name for the database that will be used with fineract. |
| spring.datasource.hikari.jdbcUrl | FINERACT_HIKARI_JDBC_URL | jdbc:mariadb://localhost:3306/fineract_tenants | The database connection string for the database with tenant information that will be used with fineract. |
| spring.datasource.hikari.username | FINERACT_HIKARI_USERNAME | root | The username for the database with tenant information that will be used with fineract |
| spring.datasource.hikari.password | FINERACT_HIKARI_PASSWORD | mysql | The password for the database with tenant information that will be used with fineract |
| spring.datasource.hikari.minimumIdle | FINERACT_HIKARI_MINIMUM_IDLE | 3 | The minimum number of connections in hakari pool that will be maintained when the system is idle |
| spring.datasource.hikari.maximumPoolSize | FINERACT_HIKARI_MAXIMUM_POOL_SIZE | 10 | The maximum number of connections that hikari can create in the pool. |
| spring.datasource.hikari.idleTimeout | FINERACT_HIKARI_IDLE_TIMEOUT | 60000 | The maximum time in milliseconds that a connection is allowed to sit idle in the pool. |
| spring.datasource.hikari.connectionTimeout | FINERACT_HIKARI_CONNECTION_TIMEOUT | 20000 | The maximum time in milliseconds that hikari will wait for a connection to be established. |
| spring.datasource.hikari.connectionTestquery | FINERACT_HIKARI_TEST_QUERY | SELECT 1 | The query that will be used to test the database connection. |
| spring.datasource.hikari.autoCommit | FINERACT_HIKARI_AUTO_COMMIT | true | If set to true, the connections in the pool will be in auto-commit mode. |
| spring.datasource.hikari.dataSourceProperties['cachePrepStmts'] | FINERACT_HIKARI_DS_PROPERTIES_CACHE_PREP_STMTS | true | If set to true, hikari caches compiled SQL statements to avoid the overhead of re-parsing and re-compiling SQL queries. |
| spring.datasource.hikari.dataSourceProperties['prepStmtCacheSize'] | FINERACT_HIKARI_DS_PROPERTIES_PREP_STMT_CACHE_SIZE | 250 | The maximum number of prepared statements that hikari can cache. |
| spring.datasource.hikari.dataSourceProperties['prepStmtCacheSqlLimit'] | FINERACT_HIKARI_DS_PROPERTIES_PREP_STMT_CACHE_SQL_LIMIT | 2048 | This property sets the upper limit for the size of individual SQL queries that can be stored in the cache. If a SQL query exceeds this limit in terms of character length, it will not be cached, even if caching is enabled. |
| spring.datasource.hikari.dataSourceProperties['useServerPrepStmts'] | FINERACT_HIKARI_DS_PROPERTIES_USE_SERVER_PREP_STMTS | true | This property determines if the connection should leverage server-side prepared statements rather than client-side ones. |
| spring.datasource.hikari.dataSourceProperties['useLocalSessionState'] | FINERACT_HIKARI_DS_PROPERTIES_USE_LOCAL_SESSION_STATE | true | This property allows the connection pool to locally track changes to session-specific properties (like character sets or time zones) rather than sending these queries to the database repeatedly. |
| spring.datasource.hikari.dataSourceProperties['rewriteBatchedStatements'] | FINERACT_HIKARI_DS_PROPERTIES_REWRITE_BATCHED_STATEMENTS | true | This property, when set to true, allows the JDBC driver to rewrite batched SQL statements into a more efficient single query format before sending them to the database. |
| spring.datasource.hikari.dataSourceProperties['cacheResultSetMetadata'] | FINERACT_HIKARI_DS_PROPERTIES_CACHE_RESULT_SET_METADATA | true | This property, when set to true, enables the caching of metadata for ResultSet objects. This metadata includes details such as column names, types, and other relevant schema information. |
| spring.datasource.hikari.dataSourceProperties['cacheServerConfiguration'] | FINERACT_HIKARI_DS_PROPERTIES_CACHE_SERVER_CONFIGURATION | true | When set to true, this property allows the JDBC driver to cache the server configuration settings, which include properties such as session state, character sets, and other configuration details relevant to the database server. |
| spring.datasource.hikari.dataSourceProperties['elideSetAutoCommits'] | FINERACT_HIKARI_DS_PROPERTIES_ELIDE_SET_AUTO_COMMITS | true | When set to true, this property prevents the JDBC driver from issuing a SET autocommit command on the database connection during its initialization. |
| spring.datasource.hikari.dataSourceProperties['maintainTimeStats'] | FINERACT_HIKARI_DS_PROPERTIES_MAINTAIN_TIME_STATS | false | When set to true, this property enables HikariCP to track and maintain statistics regarding various timing metrics related to connection pool operations, such as connection acquisition times. |
| spring.datasource.hikari.dataSourceProperties['logSlowQueries'] | FINERACT_HIKARI_DS_PROPERTIES_LOG_SLOW_QUERIES | true | When set to true, this property enables HikariCP to log SQL queries that exceed a specified execution time threshold, allowing developers and administrators to identify and analyze performance issues related to slow-running queries. |
| spring.datasource.hikari.dataSourceProperties['dumpQueriesOnException'] | FINERACT_HIKARI_DS_PROPERTIES_DUMP_QUERIES_IN_EXCEPTION | true | When set to true, this property instructs HikariCP to log the SQL statements that caused exceptions during execution. This includes capturing the query text and any associated parameters. |

### SSL Properties

| Name | Env Variable | Default Value | Description |
| --- | --- | --- | --- |
| server.ssl.enabled | FINERACT_SERVER_SSL_ENABLED | true | When set to true, SSL (Secure Sockets Layer) or TLS (Transport Layer Security) will be enabled for the server. |
| server.ssl.protocol | FINERACT_SERVER_SSL_PROTOCOL | TLS | This property allows you to define specific SSL/TLS protocol version the server will use when establishing secure connections. Common protocols include TLSv1.2, TLSv1.3, etc. |
| server.ssl.ciphers | FINERACT_SERVER_SSL_CIPHERS | TLS_RSA_WITH_AES_128_CBC_SHA256 | This property allows you to control the cipher suites that fineract will accept for secure connections |
| server.ssl.enabled-protocols | FINERACT_SERVER_SSL_PROTOCOLS | TLSv1.2 | This property allows you to define a list of SSL/TLS protocol versions that the server will support when establishing secure connections |
| server.ssl.key-store | FINERACT_SERVER_SSL_KEY_STORE | classpath:keystore.jks | The property is used to specify the location of the SSL key store file that contains the server’s private key and the associated certificate |
| server.ssl.key-store-password | FINERACT_SERVER_SSL_KEY_STORE_PASSWORD | openmf | The property defines the password for the keystore specified under property **server.ssl.key-store** |

### Authentication Properties

| Name | Env Variable | Default Value | Description |
| --- | --- | --- | --- |
| fineract.security.basicauth.enabled | FINERACT_SECURITY_BASICAUTH_ENABLED | true | When set to true, the supported authentication method will be basic authentication. |
| fineract.security.oauth2.enabled | FINERACT_SECURITY_OAUTH_ENABLED | false | When set to true, the supported authentication method will be OAuth. |
| fineract.security.2fa.enabled | FINERACT_SECURITY_2FA_ENABLED | false | Set the value to true enable two-factor authentication. For this to work as expected, ensure that you have set the correct email/sms configuration |
| spring.security.oauth2.resourceserver.jwt.issuer-uri | FINERACT_SERVER_OAUTH_RESOURCE_URL | [localhost:9000/auth/realms/fineract](http://localhost:9000/auth/realms/fineract) | If OAuth is enabled and a custom resouce server (different from what is provided) is required, set the issuer-uri here. |

### Tomcat Properties

| Name | Env Variable | Default Value | Description |
| --- | --- | --- | --- |
| server.tomcat.accept-count | FINERACT_SERVER_TOMCAT_ACCEPT_COUNT | 100 | The property specifies the maximum number of concurrent connection requests that embedded Tomcat can queue. If this limit is reached, incoming connection requests will be rejected. |
| server.tomcat.accesslog.enabled | FINERACT_SERVER_TOMCAT_ACCESSLOG_ENABLED | false | If set to true, tomcat will log access requests to file |
| server.tomcat.max-connections | FINERACT_SERVER_TOMCAT_MAX_CONNECTIONS | 8192 | Sets the maximum number of simultaneous connections Tomcat can handle. |
| server.tomcat.max-http-form-post-size | FINERACT_SERVER_TOMCAT_MAX_HTTP_FORM_POST_SIZE | 2MB | The property in sets the maximum size of HTTP POST requests that Tomcat can handle |
| server.tomcat.max-keep-alive-requests | FINERACT_SERVER_TOMCAT_MAX_KEEP_ALIVE_REQUESTS | 100 | The property specifies the maximum number of HTTP requests that can be sent over a single persistent connection (HTTP Keep-Alive) before Tomcat closes the connection |
| server.tomcat.threads.max | FINERACT_SERVER_TOMCAT_THREADS_MAX | 200 | The property sets the maximum number of threads that Tomcat can use to process requests |
| server.tomcat.threads.min-spare | FINERACT_SERVER_TOMCAT_THREADS_MIN_SPARE | 10 | The property specifies the minimum number of spare (idle) threads that Tomcat should maintain |

### Kafka Properties

| Name | Env Variable | Default Value | Description |
| --- | --- | --- | --- |
| fineract.remote-job-message-handler.kafka.enabled | FINERACT_REMOTE_JOB_MESSAGE_HANDLER_KAFKA_ENABLED | false | Enables or disables Kafka for remote job execution. If Kafka is enabled then JMS shall be disabled. |
| fineract.remote-job-message-handler.kafka.topic.auto-create | FINERACT_REMOTE_JOB_MESSAGE_HANDLER_KAFKA_TOPIC_AUTO_CREATE | true | Enables topic auto creation. In case the auto creation of the topic is disabled please make sure that the replica and the partition count is properly configured. |
| fineract.remote-job-message-handler.kafka.topic.name | FINERACT_REMOTE_JOB_MESSAGE_HANDLER_KAFKA_TOPIC_NAME | job-topic | Name of the topic where partitioned tasks are sent to |
| fineract.remote-job-message-handler.kafka.topic.replicas | FINERACT_REMOTE_JOB_MESSAGE_HANDLER_KAFKA_TOPIC_REPLICAS | 1 | Number of the replicas |
| fineract.remote-job-message-handler.kafka.topic.partitions | FINERACT_REMOTE_JOB_MESSAGE_HANDLER_KAFKA_TOPIC_PARTITIONS | 10 | Number of partitions |
| fineract.remote-job-message-handler.kafka.bootstrap-servers | FINERACT_REMOTE_JOB_MESSAGE_HANDLER_KAFKA_BOOTSTRAP_SERVERS | localhost:9092 | Comma separated list of bootstrap servers |
| fineract.remote-job-message-handler.kafka.consumer.group-id | FINERACT_REMOTE_JOB_MESSAGE_HANDLER_KAFKA_CONSUMER_GROUPID | fineract-consumer-group-id | Group ID of the Consumer |
| fineract.remote-job-message-handler.kafka.consumer.extra-properties-key-value-separator | FINERACT_REMOTE_JOB_MESSAGE_HANDLER_KAFKA_CONSUMER_EXTRA_PROPERTIES_SEPARATOR | = | Defines key and value separator for consumer,e.g.: key=value |
| fineract.remote-job-message-handler.kafka.consumer.extra-properties-separator | FINERACT_REMOTE_JOB_MESSAGE_HANDLER_KAFKA_CONSUMER_EXTRA_PROPERTIES_SEPARATOR | \| | Defines item separator for consumer, e.g.: key1=value1\|key2=value2 |
| fineract.remote-job-message-handler.kafka.consumer.extra-properties | FINERACT_REMOTE_JOB_MESSAGE_HANDLER_KAFKA_CONSUMER_EXTRA_PROPERTIES |  | #holds list of key value pairs using the above defined separators for consumer:  key1=value1\|key2=value2\|…​\|keyn=valuen |
| fineract.remote-job-message-handler.kafka.producer.extra-properties-key-value-separator | FINERACT_REMOTE_JOB_MESSAGE_HANDLER_KAFKA_PRODUCER_EXTRA_PROPERTIES_KEY_VALUE_SEPARATOR | = | Defines key and value separator for producer,e.g.: key=value |
| fineract.remote-job-message-handler.kafka.producer.extra-properties-separator | FINERACT_REMOTE_JOB_MESSAGE_HANDLER_KAFKA_PRODUCER_EXTRA_PROPERTIES_SEPARATOR | \| | Defines item separator for producer, e.g.: key1=value1\|key2=value2 |
| fineract.remote-job-message-handler.kafka.producer.extra-properties | FINERACT_REMOTE_JOB_MESSAGE_HANDLER_KAFKA_PRODUCER_EXTRA_PROPERTIES |  | #holds list of key value pairs using the above defined separators for producer:  key1=value1\|key2=value2\|…​\|keyn=valuen |
| fineract.remote-job-message-handler.kafka.admin.extra-properties-key-value-separator | FINERACT_REMOTE_JOB_MESSAGE_HANDLER_KAFKA_ADMIN_EXTRA_PROPERTIES_KEY_VALUE_SEPARATOR | = | Defines key and value separator for admin,e.g.: key=value |
| fineract.remote-job-message-handler.kafka.admin.extra-properties-separator | FINERACT_REMOTE_JOB_MESSAGE_HANDLER_KAFKA_ADMIN_EXTRA_PROPERTIES_SEPARATOR | \| | Defines item separator for admin, e.g.: key1=value1\|key2=value2 |
| fineract.remote-job-message-handler.kafka.admin.extra-properties | FINERACT_REMOTE_JOB_MESSAGE_HANDLER_KAFKA_ADMIN_EXTRA_PROPERTIES |  | #holds list of key value pairs using the above defined separators for admin:  key1=value1\|key2=value2\|…​\|keyn=valuen |

| Name | Env Variable | Default Value | Description |
| --- | --- | --- | --- |
| fineract.events.external.producer.kafka.enabled | FINERACT_EXTERNAL_EVENTS_KAFKA_ENABLED | false | Enables disables Kafka for External Events. If Kafka is enabled then JMS shall be disabled. |
| fineract.events.external.producer.kafka.timeout-in-seconds | FINERACT_EXTERNAL_EVENTS_KAFKA_TIMEOUT_IN_SECONDS | 10 | Timeout for Kafka confirming the messages written in the topic |
| fineract.events.external.producer.kafka.topic.auto-create | FINERACT_EXTERNAL_EVENTS_KAFKA_TOPIC_AUTO_CREATE | true | Enables topic auto creation. In case the auto creation of the topic is disabled please make sure that the replica and the partition count is properly configured. |
| fineract.events.external.producer.kafka.topic.name | FINERACT_EXTERNAL_EVENTS_KAFKA_TOPIC_NAME | external-events | Name of the topic where external events are sent to |
| fineract.events.external.producer.kafka.topic.replicas | FINERACT_EXTERNAL_EVENTS_KAFKA_TOPIC_REPLICAS | 1 | Number of the replicas |
| fineract.events.external.producer.kafka.topic.partitions | FINERACT_EXTERNAL_EVENTS_KAFKA_TOPIC_PARTITIONS | 10 | Number of partitions |
| fineract.events.external.producer.kafka.bootstrap-servers | FINERACT_EXTERNAL_EVENTS_KAFKA_BOOTSTRAP_SERVERS | localhost:9092 | Comma separated list of Kafka bootstrap servers |
| fineract.events.external.producer.kafka.producer.extra-properties-separator | FINERACT_EXTERNAL_EVENTS_KAFKA_PRODUCER_EXTRA_PROPERTIES_SEPARATOR | \| | Defines item separator for producer,e.g.: key=value |
| fineract.events.external.producer.kafka.producer.extra-properties-key-value-separator | FINERACT_EXTERNAL_EVENTS_KAFKA_PRODUCER_EXTRA_PROPERTIES_KEY_VALUE_SEPARATOR | = | Defines key and value separator for producer client |
| fineract.events.external.producer.kafka.producer.extra-properties | FINERACT_EXTERNAL_EVENTS_KAFKA_PRODUCER_EXTRA_PROPERTIES | linger.ms=10\|batch.size=16384 | Defines the extra properties for external event producer clients. Optimization for sending out large volume of messages. Increases Batch buffer size and batching time window. |
| fineract.events.external.producer.kafka.admin.extra-properties-separator | FINERACT_EXTERNAL_EVENTS_KAFKA_ADMIN_EXTRA_PROPERTIES_SEPARATOR | \| | Defines item separator for admin client. |
| fineract.events.external.producer.kafka.admin.extra-properties-key-value-separator | FINERACT_EXTERNAL_EVENTS_KAFKA_ADMIN_EXTRA_PROPERTIES_KEY_VALUE_SEPARATOR | = | Defines key and value separator for admin client |
| fineract.events.external.producer.kafka.admin.extra-properties | FINERACT_EXTERNAL_EVENTS_KAFKA_ADMIN_EXTRA_PROPERTIES |  | Defines the extra properties for external event admin clients |

### Metrics Properties

For further understanding of the configurations properties related to metrics, refer to [Springboot metrics docs](https://docs.spring.io/spring-boot/docs/2.0.5.RELEASE/reference/html/production-ready-metrics.html)

| Name | Env Variable | Default Value | Description |
| --- | --- | --- | --- |
| management.info.git.mode |  | FULL | Mode for displaying Git information in the `/info` endpoint. |
| management.endpoints.web.exposure.include | FINERACT_MANAGEMENT_ENDPOINT_WEB_EXPOSURE_INCLUDE | health,info,prometheus | Comma-separated list of endpoints that should be exposed over the web. |
| management.tracing.enabled | FINERACT_MANAGEMENT_METRICS_TAGS_APPLICATION | fineract | Whether tracing is enabled. |
| management.metrics.distribution.percentiles-histogram.http.server.requests | FINERACT_MANAGEMENT_METRICS_DISTRIBUTION_HTTP_SERVER_REQUESTS | false | Whether to publish percentile histograms for HTTP server requests. |
| management.otlp.metrics.export.url | FINERACT_MANAGEMENT_OLTP_METRICS_EXPORT_URL | [tempo:4318/v1/traces](http://tempo:4318/v1/traces) | URL to export OTLP metrics. |
| management.otlp.metrics.export.aggregationTemporality | FINERACT_MANAGEMENT_OLTP_METRICS_EXPORT_AGGREGATION_TEMPORALITY | cumulative | Aggregation temporality for OTLP metrics export. |
| management.prometheus.metrics.export.enabled | FINERACT_MANAGEMENT_PROMETHEUS_ENABLED | false | Whether to enable Prometheus metrics export. |
| spring.cloud.aws.cloudwatch.enabled | FINERACT_MANAGEMENT_CLOUDWATCH_ENABLED | false | Whether to enable AWS CloudWatch integration. |
| management.metrics.export.cloudwatch.enabled | FINERACT_MANAGEMENT_CLOUDWATCH_ENABLED | false | Whether to enable CloudWatch metrics export. |
| management.metrics.export.cloudwatch.namespace | FINERACT_MANAGEMENT_CLOUDWATCH_NAMESPACE | fineract | Namespace for CloudWatch metrics. |
| management.metrics.export.cloudwatch.step | FINERACT_MANAGEMENT_CLOUDWATCH_STEP | 1m | Step size for CloudWatch metrics export. |

### AWS Configuration Properties

For further understanding of the configuration properties related to AWS, refer to [Spring Cloud AWS documentation](https://docs.awspring.io/spring-cloud-aws/docs/current/reference/html/index.html).

| Name | Env Variable | Default Value | Description |
| --- | --- | --- | --- |
| spring.cloud.aws.endpoint | FINERACT_AWS_ENDPOINT |  | The AWS service endpoint. |
| spring.cloud.aws.region.static | FINERACT_AWS_REGION_STATIC | us-east-1 | The static region for AWS services. |
| spring.cloud.aws.credentials.access-key | FINERACT_AWS_CREDENTIALS_ACCESS_KEY |  | The AWS access key. |
| spring.cloud.aws.credentials.secret-key | FINERACT_AWS_CREDENTIALS_SECRET_KEY |  | The AWS secret key. |
| spring.cloud.aws.credentials.instance-profile | FINERACT_AWS_CREDENTIALS_INSTANCE_PROFILE | false | Whether to use the instance profile for credentials. |
| spring.cloud.aws.credentials.profile.name | FINERACT_AWS_CREDENTIALS_PROFILE_NAME |  | The name of the AWS credentials profile. |
| spring.cloud.aws.credentials.profile.path | FINERACT_AWS_CREDENTIALS_PROFILE_PATH |  | The path to the AWS credentials profile. |

### Resilience4j Properties

For a deeper understanding of resilience4j, refer to the [Official website](https://resilience4j.readme.io/docs/getting-started)

| Name | Env Variable | Default Value | Description |
| --- | --- | --- | --- |
| fineract.retry.instances.executeCommand.max-attempts | FINERACT_COMMAND_PROCESSING_RETRY_MAX_ATTEMPTS | 3 | The number of attempts that resilience4j will attempt to execute a command after a failed execution. Refer to  org. apache. fineract. commands. service. SynchronousCommandProcessingService#executeCommand for more details |
| fineract.retry.instances.executeCommand.wait-duration | FINERACT_COMMAND_PROCESSING_RETRY_WAIT_DURATION | 1s | The fixed time value that the retry instance will wait before the next attempt can be made to execute a command |
| fineract.retry.instances.executeCommand.enable-exponential-backoff | FINERACT_COMMAND_PROCESSING_RETRY_ENABLE_EXPONENTIAL_BACKOFF | true | If set to true, the wait-duration will increase exponentially between each retry to execute a command |
| fineract.retry.instances.executeCommand.exponential-backoff-multiplier | FINERACT_COMMAND_PROCESSING_RETRY_EXPONENTIAL_BACKOFF_MULTIPLIER | 3 | The multiplier for exponential backoff, this is useful only when enable-exponential-backoff is set to true |
| fineract.retry.instances.executeCommand.retryExceptions | FINERACT_COMMAND_PROCESSING_RETRY_EXCEPTIONS | org.springframework.dao.ConcurrencyFailureException,org.eclipse.persistence.exceptions.OptimisticLockException,jakarta.persistence.OptimisticLockException,org.springframework.orm.jpa.JpaOptimisticLockingFailureException,org.apache.fineract.infrastructure.core.exception.IdempotentCommandProcessUnderProcessingException | This property specifies the list of exceptions that the execute command retry instance will retry on |
| resilience4j.retry.instances.processJobDetailForExecution.max-attempts | FINERACT_PROCESS_JOB_DETAIL_RETRY_MAX_ATTEMPTS | 3 | The number of attempts that resilience4j will attempt to process job details for execution. Refer to org.apache.fineract.infrastructure.jobs.service.JobRegisterServiceImpl#processJobDetailForExecution for more details |
| resilience4j.retry.instances.processJobDetailForExecution.wait-duration | FINERACT_PROCESS_JOB_DETAIL_RETRY_WAIT_DURATION | 1s | The fixed time value that the retry instance will wait before the next attempt can be made |
| resilience4j.retry.instances.processJobDetailForExecution.enable-exponential-backoff | FINERACT_PROCESS_JOB_DETAIL_RETRY_ENABLE_EXPONENTIAL_BACKOFF | true | If set to true, the wait-duration will increase exponentially between each retry to process job detail |
| resilience4j.retry.instances.processJobDetailForExecution.exponential-backoff-multiplier | FINERACT_PROCESS_JOB_DETAIL_RETRY_EXPONENTIAL_BACKOFF_MULTIPLIER | 2 | The multiplier for exponential backoff, this is useful only when enable-exponential-backoff is set to true |
| resilience4j.retry.instances.recalculateInterest.max-attempts | FINERACT_PROCESS_RECALCULATE_INTEREST_RETRY_MAX_ATTEMPTS | 3 | The number of attempts that resilience4j will attempt to run recalculate interest. Refer to  org.apache.fineract.portfolio.loanaccount.service. LoanWritePlatformServiceJpaRepositoryImpl#recalculateInterest for more details |
| resilience4j.retry.instances.recalculateInterest.wait-duration | FINERACT_PROCESS_RECALCULATE_INTEREST_RETRY_WAIT_DURATION | 1s | The fixed time value that the retry instance will wait before the next attempt can be made |
| resilience4j.retry.instances.recalculateInterest.enable-exponential-backoff | FINERACT_PROCESS_RECALCULATE_INTEREST_RETRY_ENABLE_EXPONENTIAL_BACKOFF | true | If set to true, the wait-duration will increase exponentially between each retry to recalculate interest |
| resilience4j.retry.instances.recalculateInterest.exponential-backoff-multiplier | FINERACT_PROCESS_RECALCULATE_INTEREST_RETRY_EXPONENTIAL_BACKOFF_MULTIPLIER | 2 | The multiplier for exponential backoff, this is useful only when enable-exponential-backoff is set to true |
| resilience4j.retry.instances.recalculateInterest.retryException | FINERACT_PROCESS_RECALCULATE_INTEREST_RETRY_EXCEPTIONS | org.springframework.dao.ConcurrencyFailureException,org.eclipse.persistence.exceptions.OptimisticLockException,jakarta.persistence.OptimisticLockException,org.springframework.orm.jpa.JpaOptimisticLockingFailureException | This property specifies the list of exceptions that the recalculateInterest retry instance will retry on |
| resilience4j.retry.instances.postInterest.max-attempts | FINERACT_PROCESS_POST_INTEREST_RETRY_MAX_ATTEMPTS | 3 | The number of attempts that resilience4j will attempt to run post interest. Refer to  org.apache.fineract.portfolio.loanaccount.service. LoanWritePlatformServiceJpaRepositoryImpl#postInterest for more details |
| resilience4j.retry.instances.postInterest.wait-duration= | FINERACT_PROCESS_POST_INTEREST_RETRY_WAIT_DURATION | 1s | The fixed time value that the retry instance will wait before the next attempt can be made |
| resilience4j.retry.instances.postInterest.enable-exponential-backoff | FINERACT_PROCESS_POST_INTEREST_RETRY_ENABLE_EXPONENTIAL_BACKOFF | true | If set to true, the wait-duration will increase exponentially between each retry to post interest |
| resilience4j.retry.instances.postInterest.exponential-backoff-multiplier | FINERACT_PROCESS_POST_INTEREST_RETRY_EXPONENTIAL_BACKOFF_MULTIPLIER | 2 | The multiplier for exponential backoff, this is useful only when enable-exponential-backoff is set to true |
| resilience4j.retry.instances.postInterest.retryExceptions | FINERACT_PROCESS_POST_INTEREST_RETRY_EXCEPTIONS | org.springframework.dao.ConcurrencyFailureException,org.eclipse.persistence.exceptions.OptimisticLockException,jakarta.persistence.OptimisticLockException,org.springframework.orm.jpa.JpaOptimisticLockingFailureException | This property specifies the list of exceptions that the post interest retry instance will retry on |