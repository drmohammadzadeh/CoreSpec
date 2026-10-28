---
source_url: https://fineract.apache.org/docs/1.14.0#_security
title: "Security"
depth: 2
crawled_at: 2026-10-28T13:56:51.858405+00:00
parent_url: https://fineract.apache.org/docs/1.14.0
---

## Security

Fineract is **secure by design**. It is designed and built from the ground up to accept, manage, and present data securely. This chapter will detail its various security-related features and settings, along with best practices for secure deployment.

If you believe you have found a security vulnerability in Fineract itself, [let us know privately](https://fineract.apache.org/#contribute).

Your task as bank CTO, sysadmin, vendor, or other entity responsible for hosting Fineract securely is to thoroughly consider these sections and thoughtfully apply them in your work. While a Fineract release *is* secure by design, it is *not* sufficient for a sysadmin to simply start it up and hope for the best. Careful steps must be taken to ensure a deployment is and remains secure despite software environment changes, attacks, staff transitions, and anything else that may arise.

We’ll first cover the various supported authentication schemes and will continue on to recommendations for securing a Fineract deployment.

> [!NOTE]
> The HTTP Basic and OAuth authentication schemes are mutually exclusive. You can’t enable them both at the same time. Fineract checks these settings on startup and will fail if more than one authentication scheme is enabled.

### HTTP Basic Authentication

By default Fineract is configured with a HTTP Basic Authentication scheme, so you actually don’t have to do anything if you want to use it. But if you would like to explicitly choose this authentication scheme then there are two ways to enable it:

1. Use environment variables (best choice if you run with Docker Compose):
  
  
  
  
  ```bash
  FINERACT_SECURITY_BASICAUTH_ENABLED=true
  FINERACT_SECURITY_OAUTH_ENABLED=false
  ```
2. Use JVM parameters (best choice if you run the Spring Boot JAR):
  
  
  
  
  ```bash
  java -Dfineract.security.basicauth.enabled=true -Dfineract.security.oauth2.enabled=false -jar fineract-provider.jar
  ```

### OAuth

Fineract has basic OAuth support based on Spring Boot Security.

This can be enabled at runtime in one of two ways:

1. Use environment variables (best choice if you run with Docker Compose):
  
  
  
  
  ```bash
  FINERACT_SECURITY_BASICAUTH_ENABLED=false
  FINERACT_SECURITY_OAUTH_ENABLED=true
  FINERACT_SERVER_OAUTH_RESOURCE_URL=http://localhost:9000/realms/fineract
  ```
2. Use JVM parameters (best choice if you run the Spring Boot JAR):
  
  
  
  
  ```bash
  java -Dfineract.security.basicauth.enabled=false -Dfineract.security.oauth2.enabled=true -jar fineract-provider.jar
  ```

Here’s how to test OAuth with [Keycloak](https://www.keycloak.org).
The steps required for other OAuth providers will be similar.

#### Set up Keycloak

1. From terminal, run: `docker run -p 9000:8080 -e KC_BOOTSTRAP_ADMIN_USERNAME=admin -e KC_BOOTSTRAP_ADMIN_PASSWORD=admin quay.io/keycloak/keycloak:26.2.5 start-dev`
2. Go to URL 'http://localhost:9000/admin' and login with admin/admin
3. Click 'Manage realms', then 'Create realm'
4. Enter name `fineract` for the realm name
5. Click on tab 'Users' on the left, then 'Create new user' with username `mifos`, email `test@example.com`, First name `Mifos`, Last name `User`
6. Click on tab 'Credentials' at the top, and set password to `password`, turning 'temporary' setting to off
7. Click on tab 'Clients' on the left, and create client with ID `community-app`
8. In Settings tab, set 'Valid redirect URIs' to `localhost`, enable 'Client authentication', check 'Direct access grants'
9. Click 'Save' and a 'Credentials' tab will appear
10. In Credentials tab, copy string in field 'secret' as this will be needed in the step to request the access token

Finally we need to change Keycloak configuration so that it uses the username as a subject of the token:

1. Choose client `community-app` in the tab 'Clients'
2. Click on tab 'Client scopes', then `community-app-dedicated`
3. Go to tab 'Mappers', click 'Configure a new mapper' and choose 'User Property'
4. Enter `usernameInSub` as 'Name'
5. Enter `username` into the field 'Property' and `sub` into the field 'Token Claim Name'

You are now ready to test out OAuth:

#### Retrieve an access token from Keycloak

```bash
curl --request POST \
  "$FINERACT_SERVER_OAUTH_RESOURCE_URL/protocol/openid-connect/token" \
  --header 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode 'username=mifos' \
  --data-urlencode 'password=password' \
  --data-urlencode 'client_id=community-app' \
  --data-urlencode 'grant_type=password' \
  --data-urlencode 'client_secret=<enter the client secret from credentials tab>'
```

The reply should contain a field `access_token`. Copy the field’s value and use it in the API call below:

#### Invoke APIs and passAuthorization: bearer …​header

```bash
curl --insecure \
  'https://localhost:8443/fineract-provider/api/v1/offices' \
  --header 'Fineract-Platform-TenantId: default' \
  --header 'Authorization: bearer <enter the value of the access_token field>'
```

> [!NOTE]
> See also [fineract.apache.org/docs/legacy/#authentication_oauth](https://fineract.apache.org/docs/legacy/#authentication_oauth)

### Two-factor authentication

You can enable 2FA authentication. Depending on how you start Fineract add the following:

1. Use environment variables (best choice if you run with Docker Compose):
  
  
  
  
  ```bash
  FINERACT_SECURITY_2FA_ENABLED=true
  ```
2. Use JVM parameter (best choice if you run the Spring Boot JAR):
  
  
  
  
  ```bash
  java -Dfineract.security.2fa.enabled=true -jar fineract-provider.jar
  ```

### Securing Fineract

This section covers best practices in securing the use of Fineract.

Security hardening is a continuum and Fineract is adaptable to your security needs. There’s no one way to correctly deploy it and the open source project offers no warranty. It’s up to you to deploy and maintain it carefully, according to your organization’s needs and compliance requirements.

Since Fineract is a financial application with PII (personally identifiable information), it is vital that it is secured in production whenever it is setup. If you are a small financial entity, bank, credit union, microfinance organization, or non-banking financial institution, the project urges you to identify and work with the vendors that work regularly with Fineract and are regular contributors to the security fixes. In this way, we encourage a community of contributions that keep the overall solution secure. Open source gets the benefit of many people reviewing the code and suggesting issues and solutions - let’s ensure that virtuous cycle can work by supporting those working on security at Fineract.

Members of the Security team can be reached at security AT fineract.apache.org. The reporting mechanisms for vulnerabilities and exploits are there, not on the public dev list.

See apache security practices for more information. [security.apache.org](https://security.apache.org)

Also, we recommend you familiarize yourself with the OWASP foundation and the "Cheat Sheet" series [cheatsheetseries.owasp.org](https://cheatsheetseries.owasp.org)

#### Tips for securing the Fineract infrastructure

##### Run it isolated and/or disconnected

In the world of Microfinance or small banking operations (in some geographies), it is possible that you can run Fineract on a private network, or isolated from the internet by being hosted locally and securing all connections. This could involve establishing a VPN with limited ports open, and only accepting connections within that VPN. At the far end of this spectrum, is running it isolated and air-gapped as a backend accounting system, where there is no internet connection on that device. In such scenarios, you are limiting the vectors of attack to just those employees you give access to. You are also limiting the functionality to accounting and basic operations, so this is rarely appropriate.  Even in these scenarios, it is important that you establish reviews of logs and accounts on a periodic basis to determine if any internal fraud is occurring. Such things should be part of your operational manual. There are a number of resources available for this topic, please find them online. For Fineract in particular, be mindful of the set up of approvals and and the access you give to each person or role in your organization

##### Running it connected but behind a firewall

It should be clear that running it on the internet directly, without API monitoring and filtering, is a bad idea. This is especially true if your Fineract instance is connected to a payment mechanism of any kind. Imagine an exploit being used to gain access and then to send funds from an account to an outside merchant or bank. An attacker could drain an account before you can detect the issue.  And, then it will depend on the payment scheme rules whether any of those funds are recoverable.

There are multiple ways to enhance the security that is built into Fineract, but none of them are bulletproof and so you must have defense in depth. One key thing is to run the Fineract instance behind an API gateway, and to prevent certain API patterns or calls that are likely to be fraudulent. The important thing is to recognize that while you may not be a target institution now, at any moment this can change, and your IP will be listed on the dark web as a potential target for exploit. Your IT team must also have ways to quickly turn off services to limit the damage.

It is recommended to run it with at least API Gateway, WAF (Web Application Firewall) and SQL Injection filtering tool if connecting to the internet. Fineract must be hardened to run in production.

##### Fraud prevention

Even if you have secured your infrastructure, you will need the ability to monitor fraudulent traffic, and then to stop that fraud in real time. Fraud can occur even when your infrastructure is good, but a user account has been accessed through a phishing attack or similar vector. And, in the world of real time payments and multiple payment types and channels, there is a need for additional real time monitoring, and inline processing of potential fraudulent transactions. Detection and blocking needs to occur in real time and then resolution can occur more leisurely with additional manual and help desk interventions.

If you are a small institution and you are getting into this situation, you should consider having holds on all payment and transfers built into your process, until you can enable effective tools.

There are a number of fraud prevention tools that are available in market from fraud prevention vendors. When looking for solution providers, the ideal scenario is a vendor with longevity and a track record in your market for detecting recent fraudulent activities. Pattern detection is a key part of this, and for that, it is important to be able to get enough data from your systems to identify the anomalies.

There are a number of GitHub projects that cover algorithms for conducting ML on transactions to detect anomalies. There is also an open source project, Tazama, which provides a kind of framework for your own logic and algorithms: [github.com/frmscoe/docs](https://github.com/frmscoe/docs).

Fraud exploits are on the rise, supercharged by AI tooling. AI tooling can also be used to fight these trends, but it is an ever escalating area of concern for financial providers globally.

##### Self-service APIs

It is recommended that you leave the Self Service APIs disabled to avoid any potential exploits there. Apps should not be developed to use those APIs.

There is a way to run those APIs endpoint (re-written but consistent) in a separate isolated component, where there is a way to control the ingress and egress of data. Once that component is linked up with authenticated users with a fully designed authorization scheme, then the APIs can be accessed.  This is an area of exploration by the project. Currently, Fineract should not be run in a way that allows access to those APIs. We strongly advise against using any APP that connects to those APIs without revising the architecture as described, except in a test or demo environment.

##### User Education and Training

Educating and training your team is another limb of your organizational cybersecurity defense. Equipped with engaging security awareness training sessions, end-users can be prepared with both knowledge and skills on how to identify potential security threats and react to them. You can get more information from some of the resources offered in the course during CISA Training: [www.cisa.gov](https://www.cisa.gov)

##### Regular Security Audits and Compliance Checks

Know your compliance surface. Regularly conduct routine security audits and compliance checks. This can be helpful in finding all the vulnerabilities and their fix prior to exploitation, thereby helping to reduce the exposure window. A combined automated tool with manual expert reviews provides complete coverage. There are multiple vendors available that scan for compliance with existing security standards. We don’t recommend any vendor in particular, but for pointers you can look at [owasp.org/www-community/Vulnerability_Scanning_Tools](https://owasp.org/www-community/Vulnerability_Scanning_Tools)

##### Key Management and Data Encryption Strategies

Implement strong data encryption strategies to protect sensitive information. Key management should be something that your IT team does, utilizing best practices. Just like a physical key, you should keep it in a secure location with limited access and take special care not to copy it to digital locations that can be scanned or found, including email systems. Make sure you have procedures in place.

You would probably want to encrypt the data at rest with AES-256 and in transit via TLS 1.3. Create and maintain binding standards for encryption in your organization. And remember, key management to encryption is the key. Every cloud providers provides key management services that help you manage and secure your keys.

Examples:

* [aws.amazon.com/kms/](https://aws.amazon.com/kms/)
* [cloud.google.com/docs/security/key-management-deep-dive](https://cloud.google.com/docs/security/key-management-deep-dive)
* [learn.microsoft.com/en-us/azure/security/fundamentals/key-management](https://learn.microsoft.com/en-us/azure/security/fundamentals/key-management)
* [github.com/getsops/sops](https://github.com/getsops/sops)
* [github.com/Infisical/infisical](https://github.com/Infisical/infisical)

##### Secure Coding Practices

Secure code by following secure coding practices and standards, such as OWASP’s top ten, for any kind of vulnerability at the code level. Use tools like SonarQube for finding security problems in your source code through static application security testing (SAST) prior to deploying an application. Note that SonarQube has already been integrated into our automation build process.

Apache Software Foundation has an account with SonarQube and Fineract scans can be found in that account.

##### Multi-factor Authentication (MFA)

Enhance your security layers with MFA (or 2FA: two-factor authentication). One such approach, built on three things: something the user knows (like a password), something the user has (like a security token), and something the user is (biometric verification, for example). When MFA is used, it adds another layer of security. Solutions such as Duo Security may be a good implementation for MFA.

##### Leverage Community Support

You should stay engaged with the Fineract community to stay on top of security updates, patches, and best practices. Also, look for the possibility of collaboration with cybersecurity firms that would help you increase the capability of your threat detection and response system. Such relationships may avail specialized skills, technologies, and intelligence that may strengthen the security posturing of your organization.