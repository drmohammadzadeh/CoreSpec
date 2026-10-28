---
source_url: https://fineract.apache.org/docs/1.17.0-SNAPSHOT#_custom_modules
title: "Custom Modules"
depth: 2
crawled_at: 2026-10-28T13:56:51.858405+00:00
parent_url: https://fineract.apache.org/docs/develop
---

## Custom Modules

> [!NOTE]
> Currently, modules are a proof of concept feature in Fineract.

### Introduction

Creating customizations for Fineract services is easy. The method described here will work both with our future module guidelines (aka "clean room" modules) and with the intermediary solution we will put in place to avoid major refactorings.

The folder structure for modules is based on a convention that ensures that your extensions don’t clash with Fineract’s internals. This is to make sure that your downstream forks of Fineract are easy to sync. In the past we had all kinds of strategies to add custom code - including editing existing sources in `fineract-provider`. This is not recommended.

> [!IMPORTANT]
> At the moment the only service(s) we prepared to be overridden/replaced are `org.apache.fineract.portfolio.note.service.NoteReadPlatformService` and `org.apache.fineract.portfolio.note.service.NoteWritePlatformService`. Please reach out on the developer mailing list if you need other services.

The recommended folder structure is very simple. If you follow this recommendation you’ll get some additional benefits, e. g. you don’t even have to edit `settings.gradle` to include your new custom modules. Your modules will also be automatically included in a custom Fineract Docker image build that you can use for your production deployments.

Let’s assume your company/org is called "ACME Inc." and you are trying to (fully/partially) replace an existing Fineract service, let’s say those in `org.apache.fineract.portfolio.note`. The recommended folder structure would then look something like this:

![Diagram](data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0nMS4wJyBlbmNvZGluZz0nVVRGLTgnIHN0YW5kYWxvbmU9J25vJz8+PHN2ZyBjb250ZW50U3R5bGVUeXBlPSd0ZXh0L2NzcycgaGVpZ2h0PSc1NjZweCcgcHJlc2VydmVBc3BlY3RSYXRpbz0nbm9uZScgc3R5bGU9J3dpZHRoOjUwMHB4O2hlaWdodDo1NjZweDtiYWNrZ3JvdW5kOiNGRkZGRkY7JyB2ZXJzaW9uPScxLjEnIHZpZXdCb3g9JzAgMCA1MDAgNTY2JyB3aWR0aD0nNTAwcHgnIHhtbG5zOnhsaW5rPSdodHRwOi8vd3d3LnczLm9yZy8xOTk5L3hsaW5rJyB4bWxucz0naHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmcnIHpvb21BbmRQYW49J21hZ25pZnknPjxkZWZzLz48Zz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc0MScgeD0nMTYnIHk9JzE4LjgyODEnPmN1c3RvbTwvdGV4dD48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSczMScgeD0nMjYnIHk9JzM1LjE3MjInPmFjbWU8L3RleHQ+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMjUnIHg9JzM2JyB5PSc1MS41MTYzJz5ub3RlPC90ZXh0Pjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEyJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzI1JyB4PSc0NicgeT0nNjcuODYwNCc+Y29yZTwvdGV4dD48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxNycgeD0nNTYnIHk9Jzg0LjIwNDUnPnNyYzwvdGV4dD48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScyOCcgeD0nNjYnIHk9JzEwMC41NDg3Jz5tYWluPC90ZXh0Pjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEyJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzIzJyB4PSc3NicgeT0nMTE2Ljg5MjgnPmphdmE8L3RleHQ+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTYwJyB4PSc4NicgeT0nMTMzLjIzNjknPmNvbS5hY21lLmZpbmVyYWN0Lm5vdGUuY29yZTwvdGV4dD48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScyNScgeD0nOTYnIHk9JzE0OS41ODEnPmRhdGE8L3RleHQ+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nNzAnIHg9JzEwNicgeT0nMTY1LjkyNTEnPk15RGF0YS5qYXZhPC90ZXh0Pjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEyJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzQwJyB4PSc5NicgeT0nMTgyLjI2OTInPnNlcnZpY2U8L3RleHQ+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTI3JyB4PScxMDYnIHk9JzE5OC42MTMzJz5NeUN1c3RvbVNlcnZpY2UuamF2YTwvdGV4dD48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc2NicgeD0nNTYnIHk9JzIxNC45NTc1Jz5idWlsZC5ncmFkbGU8L3RleHQ+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTE3JyB4PSc1NicgeT0nMjMxLjMwMTYnPmRlcGVuZGVuY2llcy5ncmFkbGU8L3RleHQ+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nNDAnIHg9JzQ2JyB5PScyNDcuNjQ1Nyc+c2VydmljZTwvdGV4dD48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxNycgeD0nNTYnIHk9JzI2My45ODk4Jz5zcmM8L3RleHQ+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMjgnIHg9JzY2JyB5PScyODAuMzMzOSc+bWFpbjwvdGV4dD48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScyMycgeD0nNzYnIHk9JzI5Ni42NzgnPmphdmE8L3RleHQ+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTc1JyB4PSc4NicgeT0nMzEzLjAyMjEnPmNvbS5hY21lLmZpbmVyYWN0Lm5vdGUuc2VydmljZTwvdGV4dD48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxNTQnIHg9Jzk2JyB5PSczMjkuMzY2Myc+QWNtZU5vdGVSZWFkU2VydmljZS5qYXZhPC90ZXh0Pjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEyJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzE1NicgeD0nOTYnIHk9JzM0NS43MTA0Jz5BY21lTm90ZVdyaXRlU2VydmljZS5qYXZhPC90ZXh0Pjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEyJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzY2JyB4PSc1NicgeT0nMzYyLjA1NDUnPmJ1aWxkLmdyYWRsZTwvdGV4dD48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxMTcnIHg9JzU2JyB5PSczNzguMzk4Nic+ZGVwZW5kZW5jaWVzLmdyYWRsZTwvdGV4dD48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSczOCcgeD0nNDYnIHk9JzM5NC43NDI3Jz5zdGFydGVyPC90ZXh0Pjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEyJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzE3JyB4PSc1NicgeT0nNDExLjA4NjgnPnNyYzwvdGV4dD48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScyOCcgeD0nNjYnIHk9JzQyNy40MzA5Jz5tYWluPC90ZXh0Pjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEyJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzIzJyB4PSc3NicgeT0nNDQzLjc3NTEnPmphdmE8L3RleHQ+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTczJyB4PSc4NicgeT0nNDYwLjExOTInPmNvbS5hY21lLmZpbmVyYWN0Lm5vdGUuc3RhcnRlcjwvdGV4dD48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxODcnIHg9Jzk2JyB5PSc0NzYuNDYzMyc+QWNtZU5vdGVBdXRvQ29uZmlndXJhdGlvbi5qYXZhPC90ZXh0Pjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEyJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzU2JyB4PSc1NicgeT0nNDkyLjgwNzQnPnJlc291cmNlczwvdGV4dD48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc1NicgeD0nNjYnIHk9JzUwOS4xNTE1Jz5NRVRBLUlORjwvdGV4dD48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc0MTcnIHg9Jzc2JyB5PSc1MjUuNDk1Nic+c3ByaW5nL29yZy5zcHJpbmdmcmFtZXdvcmsuYm9vdC5hdXRvY29uZmlndXJlLkF1dG9Db25maWd1cmF0aW9uLmltcG9ydHM8L3RleHQ+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nNjYnIHg9JzU2JyB5PSc1NDEuODM5Nyc+YnVpbGQuZ3JhZGxlPC90ZXh0Pjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEyJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzExNycgeD0nNTYnIHk9JzU1OC4xODM5Jz5kZXBlbmRlbmNpZXMuZ3JhZGxlPC90ZXh0PjxyZWN0IGZpbGw9J25vbmUnIGhlaWdodD0nMicgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB3aWR0aD0nMicgeD0nOScgeT0nMTMuMTcyMScvPjxyZWN0IGZpbGw9J25vbmUnIGhlaWdodD0nMicgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB3aWR0aD0nMicgeD0nMTknIHk9JzI5LjUxNjInLz48bGluZSBzdHlsZT0nc3Ryb2tlOiM4ODg4ODg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPScxMCcgeDI9JzEwJyB5MT0nMTYuMTcyMScgeTI9JzMwLjUxNjInLz48bGluZSBzdHlsZT0nc3Ryb2tlOiM4ODg4ODg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPScxMCcgeDI9JzE4JyB5MT0nMzAuNTE2MicgeTI9JzMwLjUxNjInLz48cmVjdCBmaWxsPSdub25lJyBoZWlnaHQ9JzInIHN0eWxlPSdzdHJva2U6Izg4ODg4ODtzdHJva2Utd2lkdGg6MS4wOycgd2lkdGg9JzInIHg9JzI5JyB5PSc0NS44NjAzJy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nMjAnIHgyPScyMCcgeTE9JzMyLjUxNjInIHkyPSc0Ni44NjAzJy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nMjAnIHgyPScyOCcgeTE9JzQ2Ljg2MDMnIHkyPSc0Ni44NjAzJy8+PHJlY3QgZmlsbD0nbm9uZScgaGVpZ2h0PScyJyBzdHlsZT0nc3Ryb2tlOiM4ODg4ODg7c3Ryb2tlLXdpZHRoOjEuMDsnIHdpZHRoPScyJyB4PSczOScgeT0nNjIuMjA0NCcvPjxsaW5lIHN0eWxlPSdzdHJva2U6Izg4ODg4ODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzMwJyB4Mj0nMzAnIHkxPSc0OC44NjAzJyB5Mj0nNjMuMjA0NCcvPjxsaW5lIHN0eWxlPSdzdHJva2U6Izg4ODg4ODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzMwJyB4Mj0nMzgnIHkxPSc2My4yMDQ0JyB5Mj0nNjMuMjA0NCcvPjxyZWN0IGZpbGw9J25vbmUnIGhlaWdodD0nMicgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB3aWR0aD0nMicgeD0nNDknIHk9Jzc4LjU0ODUnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiM4ODg4ODg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSc0MCcgeDI9JzQwJyB5MT0nNjUuMjA0NCcgeTI9Jzc5LjU0ODUnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiM4ODg4ODg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSc0MCcgeDI9JzQ4JyB5MT0nNzkuNTQ4NScgeTI9Jzc5LjU0ODUnLz48cmVjdCBmaWxsPSdub25lJyBoZWlnaHQ9JzInIHN0eWxlPSdzdHJva2U6Izg4ODg4ODtzdHJva2Utd2lkdGg6MS4wOycgd2lkdGg9JzInIHg9JzU5JyB5PSc5NC44OTI2Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nNTAnIHgyPSc1MCcgeTE9JzgxLjU0ODUnIHkyPSc5NS44OTI2Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nNTAnIHgyPSc1OCcgeTE9Jzk1Ljg5MjYnIHkyPSc5NS44OTI2Jy8+PHJlY3QgZmlsbD0nbm9uZScgaGVpZ2h0PScyJyBzdHlsZT0nc3Ryb2tlOiM4ODg4ODg7c3Ryb2tlLXdpZHRoOjEuMDsnIHdpZHRoPScyJyB4PSc2OScgeT0nMTExLjIzNjcnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiM4ODg4ODg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSc2MCcgeDI9JzYwJyB5MT0nOTcuODkyNicgeTI9JzExMi4yMzY3Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nNjAnIHgyPSc2OCcgeTE9JzExMi4yMzY3JyB5Mj0nMTEyLjIzNjcnLz48cmVjdCBmaWxsPSdub25lJyBoZWlnaHQ9JzInIHN0eWxlPSdzdHJva2U6Izg4ODg4ODtzdHJva2Utd2lkdGg6MS4wOycgd2lkdGg9JzInIHg9Jzc5JyB5PScxMjcuNTgwOScvPjxsaW5lIHN0eWxlPSdzdHJva2U6Izg4ODg4ODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzcwJyB4Mj0nNzAnIHkxPScxMTQuMjM2NycgeTI9JzEyOC41ODA5Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nNzAnIHgyPSc3OCcgeTE9JzEyOC41ODA5JyB5Mj0nMTI4LjU4MDknLz48cmVjdCBmaWxsPSdub25lJyBoZWlnaHQ9JzInIHN0eWxlPSdzdHJva2U6Izg4ODg4ODtzdHJva2Utd2lkdGg6MS4wOycgd2lkdGg9JzInIHg9Jzg5JyB5PScxNDMuOTI1Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nODAnIHgyPSc4MCcgeTE9JzEzMC41ODA5JyB5Mj0nMTQ0LjkyNScvPjxsaW5lIHN0eWxlPSdzdHJva2U6Izg4ODg4ODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzgwJyB4Mj0nODgnIHkxPScxNDQuOTI1JyB5Mj0nMTQ0LjkyNScvPjxsaW5lIHN0eWxlPSdzdHJva2U6Izg4ODg4ODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzkwJyB4Mj0nOTAnIHkxPScxNDYuOTI1JyB5Mj0nMTYxLjI2OTEnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiM4ODg4ODg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSc5MCcgeDI9Jzk4JyB5MT0nMTYxLjI2OTEnIHkyPScxNjEuMjY5MScvPjxyZWN0IGZpbGw9J25vbmUnIGhlaWdodD0nMicgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB3aWR0aD0nMicgeD0nODknIHk9JzE3Ni42MTMyJy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nODAnIHgyPSc4MCcgeTE9JzEzMC41ODA5JyB5Mj0nMTc3LjYxMzInLz48bGluZSBzdHlsZT0nc3Ryb2tlOiM4ODg4ODg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSc4MCcgeDI9Jzg4JyB5MT0nMTc3LjYxMzInIHkyPScxNzcuNjEzMicvPjxsaW5lIHN0eWxlPSdzdHJva2U6Izg4ODg4ODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzkwJyB4Mj0nOTAnIHkxPScxNzkuNjEzMicgeTI9JzE5My45NTczJy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nOTAnIHgyPSc5OCcgeTE9JzE5My45NTczJyB5Mj0nMTkzLjk1NzMnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiM4ODg4ODg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSc0MCcgeDI9JzQwJyB5MT0nNjUuMjA0NCcgeTI9JzIxMC4zMDE0Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nNDAnIHgyPSc0OCcgeTE9JzIxMC4zMDE0JyB5Mj0nMjEwLjMwMTQnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiM4ODg4ODg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSc0MCcgeDI9JzQwJyB5MT0nNjUuMjA0NCcgeTI9JzIyNi42NDU1Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nNDAnIHgyPSc0OCcgeTE9JzIyNi42NDU1JyB5Mj0nMjI2LjY0NTUnLz48cmVjdCBmaWxsPSdub25lJyBoZWlnaHQ9JzInIHN0eWxlPSdzdHJva2U6Izg4ODg4ODtzdHJva2Utd2lkdGg6MS4wOycgd2lkdGg9JzInIHg9JzM5JyB5PScyNDEuOTg5NycvPjxsaW5lIHN0eWxlPSdzdHJva2U6Izg4ODg4ODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzMwJyB4Mj0nMzAnIHkxPSc0OC44NjAzJyB5Mj0nMjQyLjk4OTcnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiM4ODg4ODg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSczMCcgeDI9JzM4JyB5MT0nMjQyLjk4OTcnIHkyPScyNDIuOTg5NycvPjxyZWN0IGZpbGw9J25vbmUnIGhlaWdodD0nMicgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB3aWR0aD0nMicgeD0nNDknIHk9JzI1OC4zMzM4Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nNDAnIHgyPSc0MCcgeTE9JzI0NC45ODk3JyB5Mj0nMjU5LjMzMzgnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiM4ODg4ODg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSc0MCcgeDI9JzQ4JyB5MT0nMjU5LjMzMzgnIHkyPScyNTkuMzMzOCcvPjxyZWN0IGZpbGw9J25vbmUnIGhlaWdodD0nMicgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB3aWR0aD0nMicgeD0nNTknIHk9JzI3NC42Nzc5Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nNTAnIHgyPSc1MCcgeTE9JzI2MS4zMzM4JyB5Mj0nMjc1LjY3NzknLz48bGluZSBzdHlsZT0nc3Ryb2tlOiM4ODg4ODg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSc1MCcgeDI9JzU4JyB5MT0nMjc1LjY3NzknIHkyPScyNzUuNjc3OScvPjxyZWN0IGZpbGw9J25vbmUnIGhlaWdodD0nMicgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB3aWR0aD0nMicgeD0nNjknIHk9JzI5MS4wMjInLz48bGluZSBzdHlsZT0nc3Ryb2tlOiM4ODg4ODg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSc2MCcgeDI9JzYwJyB5MT0nMjc3LjY3NzknIHkyPScyOTIuMDIyJy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nNjAnIHgyPSc2OCcgeTE9JzI5Mi4wMjInIHkyPScyOTIuMDIyJy8+PHJlY3QgZmlsbD0nbm9uZScgaGVpZ2h0PScyJyBzdHlsZT0nc3Ryb2tlOiM4ODg4ODg7c3Ryb2tlLXdpZHRoOjEuMDsnIHdpZHRoPScyJyB4PSc3OScgeT0nMzA3LjM2NjEnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiM4ODg4ODg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSc3MCcgeDI9JzcwJyB5MT0nMjk0LjAyMicgeTI9JzMwOC4zNjYxJy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nNzAnIHgyPSc3OCcgeTE9JzMwOC4zNjYxJyB5Mj0nMzA4LjM2NjEnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiM4ODg4ODg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSc4MCcgeDI9JzgwJyB5MT0nMzEwLjM2NjEnIHkyPSczMjQuNzEwMicvPjxsaW5lIHN0eWxlPSdzdHJva2U6Izg4ODg4ODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzgwJyB4Mj0nODgnIHkxPSczMjQuNzEwMicgeTI9JzMyNC43MTAyJy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nODAnIHgyPSc4MCcgeTE9JzMxMC4zNjYxJyB5Mj0nMzQxLjA1NDMnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiM4ODg4ODg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSc4MCcgeDI9Jzg4JyB5MT0nMzQxLjA1NDMnIHkyPSczNDEuMDU0MycvPjxsaW5lIHN0eWxlPSdzdHJva2U6Izg4ODg4ODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzQwJyB4Mj0nNDAnIHkxPScyNDQuOTg5NycgeTI9JzM1Ny4zOTg1Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nNDAnIHgyPSc0OCcgeTE9JzM1Ny4zOTg1JyB5Mj0nMzU3LjM5ODUnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiM4ODg4ODg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSc0MCcgeDI9JzQwJyB5MT0nMjQ0Ljk4OTcnIHkyPSczNzMuNzQyNicvPjxsaW5lIHN0eWxlPSdzdHJva2U6Izg4ODg4ODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzQwJyB4Mj0nNDgnIHkxPSczNzMuNzQyNicgeTI9JzM3My43NDI2Jy8+PHJlY3QgZmlsbD0nbm9uZScgaGVpZ2h0PScyJyBzdHlsZT0nc3Ryb2tlOiM4ODg4ODg7c3Ryb2tlLXdpZHRoOjEuMDsnIHdpZHRoPScyJyB4PSczOScgeT0nMzg5LjA4NjcnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiM4ODg4ODg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSczMCcgeDI9JzMwJyB5MT0nNDguODYwMycgeTI9JzM5MC4wODY3Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nMzAnIHgyPSczOCcgeTE9JzM5MC4wODY3JyB5Mj0nMzkwLjA4NjcnLz48cmVjdCBmaWxsPSdub25lJyBoZWlnaHQ9JzInIHN0eWxlPSdzdHJva2U6Izg4ODg4ODtzdHJva2Utd2lkdGg6MS4wOycgd2lkdGg9JzInIHg9JzQ5JyB5PSc0MDUuNDMwOCcvPjxsaW5lIHN0eWxlPSdzdHJva2U6Izg4ODg4ODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzQwJyB4Mj0nNDAnIHkxPSczOTIuMDg2NycgeTI9JzQwNi40MzA4Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nNDAnIHgyPSc0OCcgeTE9JzQwNi40MzA4JyB5Mj0nNDA2LjQzMDgnLz48cmVjdCBmaWxsPSdub25lJyBoZWlnaHQ9JzInIHN0eWxlPSdzdHJva2U6Izg4ODg4ODtzdHJva2Utd2lkdGg6MS4wOycgd2lkdGg9JzInIHg9JzU5JyB5PSc0MjEuNzc0OScvPjxsaW5lIHN0eWxlPSdzdHJva2U6Izg4ODg4ODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzUwJyB4Mj0nNTAnIHkxPSc0MDguNDMwOCcgeTI9JzQyMi43NzQ5Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nNTAnIHgyPSc1OCcgeTE9JzQyMi43NzQ5JyB5Mj0nNDIyLjc3NDknLz48cmVjdCBmaWxsPSdub25lJyBoZWlnaHQ9JzInIHN0eWxlPSdzdHJva2U6Izg4ODg4ODtzdHJva2Utd2lkdGg6MS4wOycgd2lkdGg9JzInIHg9JzY5JyB5PSc0MzguMTE5Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nNjAnIHgyPSc2MCcgeTE9JzQyNC43NzQ5JyB5Mj0nNDM5LjExOScvPjxsaW5lIHN0eWxlPSdzdHJva2U6Izg4ODg4ODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzYwJyB4Mj0nNjgnIHkxPSc0MzkuMTE5JyB5Mj0nNDM5LjExOScvPjxyZWN0IGZpbGw9J25vbmUnIGhlaWdodD0nMicgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB3aWR0aD0nMicgeD0nNzknIHk9JzQ1NC40NjMxJy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nNzAnIHgyPSc3MCcgeTE9JzQ0MS4xMTknIHkyPSc0NTUuNDYzMScvPjxsaW5lIHN0eWxlPSdzdHJva2U6Izg4ODg4ODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzcwJyB4Mj0nNzgnIHkxPSc0NTUuNDYzMScgeTI9JzQ1NS40NjMxJy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nODAnIHgyPSc4MCcgeTE9JzQ1Ny40NjMxJyB5Mj0nNDcxLjgwNzMnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiM4ODg4ODg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSc4MCcgeDI9Jzg4JyB5MT0nNDcxLjgwNzMnIHkyPSc0NzEuODA3MycvPjxyZWN0IGZpbGw9J25vbmUnIGhlaWdodD0nMicgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB3aWR0aD0nMicgeD0nNDknIHk9JzQ4Ny4xNTE0Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nNDAnIHgyPSc0MCcgeTE9JzM5Mi4wODY3JyB5Mj0nNDg4LjE1MTQnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiM4ODg4ODg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSc0MCcgeDI9JzQ4JyB5MT0nNDg4LjE1MTQnIHkyPSc0ODguMTUxNCcvPjxyZWN0IGZpbGw9J25vbmUnIGhlaWdodD0nMicgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB3aWR0aD0nMicgeD0nNTknIHk9JzUwMy40OTU1Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nNTAnIHgyPSc1MCcgeTE9JzQ5MC4xNTE0JyB5Mj0nNTA0LjQ5NTUnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiM4ODg4ODg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSc1MCcgeDI9JzU4JyB5MT0nNTA0LjQ5NTUnIHkyPSc1MDQuNDk1NScvPjxsaW5lIHN0eWxlPSdzdHJva2U6Izg4ODg4ODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzYwJyB4Mj0nNjAnIHkxPSc1MDYuNDk1NScgeTI9JzUyMC44Mzk2Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nNjAnIHgyPSc2OCcgeTE9JzUyMC44Mzk2JyB5Mj0nNTIwLjgzOTYnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiM4ODg4ODg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSc0MCcgeDI9JzQwJyB5MT0nMzkyLjA4NjcnIHkyPSc1MzcuMTgzNycvPjxsaW5lIHN0eWxlPSdzdHJva2U6Izg4ODg4ODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzQwJyB4Mj0nNDgnIHkxPSc1MzcuMTgzNycgeTI9JzUzNy4xODM3Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nNDAnIHgyPSc0MCcgeTE9JzM5Mi4wODY3JyB5Mj0nNTUzLjUyNzgnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiM4ODg4ODg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSc0MCcgeDI9JzQ4JyB5MT0nNTUzLjUyNzgnIHkyPSc1NTMuNTI3OCcvPjwvZz48L3N2Zz4=)

As soon as we can publish Fineract module JARs to Maven Central you’ll have more freedom to setup your projects (including to setup separate Git repos). But for now please follow these instructions:

1. Create a folder under `custom` and name it according to your company/organisation (e. g. `acme` if your company is `ACME Inc.`); this way your custom modules can’t clash even with other companies' modules
2. Under your company folder create a folder for the `category` or `domain` your module is targeting; e. g. "loan", "client", "account" etc.
3. Finally, setup `library` folders for the actual modules you want to create; usually that will be to replace/extend some existing service, so there could be a `service` folder, maybe even a `core` folder, e. g. if you want to add additional DTOs etc.; we have also an example for COB business steps
4. Per `category`/`domain` you should have a `starter` library; means: a Spring Boot auto-configuration setup that makes including your module in Fineract easier ("hands-free"); the necessary parts for a auto-configuration library are a Spring Java configuration class (annotated with `@Configuration`) and a text file at `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports` in your starter resource folder:
  
  
  
  
  ```properties
  com.acme.fineract.portfolio.note.starter.AcmeNoteAutoConfiguration
  ```
  
  
  
  
  
  Please make sure that your module libraries have proper `build.gradle` files:
  
  
  
  
  
  ```groovy
  description = 'ACME Fineract Note Service'
  
  group = 'com.acme.fineract'
  
  base {
      archivesName = 'acme-fineract-note-service'
  }
  
  apply from: 'dependencies.gradle'
  ```
  
  
  
  
  > [!NOTE]
  > You don’t need to edit `settings.gradle` to add your modules/libraries. If you follow above convention they’ll get included automatically.
5. The dependency.gradle file could look something like this:
  
  
  
  
  ```groovy
  dependencies {
      implementation(project(':fineract-core'))
      implementation(project(':fineract-provider'))
      compileOnly('org.springframework.boot:spring-boot-autoconfigure')
  }
  ```

> [!NOTE]
> We’ve included by default some basic and useful dependencies for all custom modules, like Slf4j, Lombok, the usual testing frameworks (JUnit, Cucumber, Mockito etc.)

> [!IMPORTANT]
> Do not include your custom module in `fineract-provider’s dependency.gradle file. This creates a circular dependency and will fail your build.

### Custom Services

> [!NOTE]
> We are still trying to figure out which internal services make most sense to be pluggable. Please join the discussion and let us know if you have a specific requirement.

#### Note Service

The Note service is responsible for …​ TBD

> [!NOTE]
> We chose the note service because it’s interface is very simple and has not many cross dependencies.

##### Interfaces

```java
package org.apache.fineract.portfolio.note.service;

import java.util.List;
import org.apache.fineract.portfolio.note.data.NoteData;

public interface NoteReadPlatformService {

    NoteData retrieveNote(Long noteId, Long resourceId, Integer noteTypeId);

    List<NoteData> retrieveNotesByResource(Long resourceId, Integer noteTypeId);
}
```

```java
package org.apache.fineract.portfolio.note.service;

import java.util.List;
import org.apache.fineract.portfolio.note.data.NoteData;

public interface NoteReadPlatformService {

    NoteData retrieveNote(Long noteId, Long resourceId, Integer noteTypeId);

    List<NoteData> retrieveNotesByResource(Long resourceId, Integer noteTypeId);
}
```

##### Configuration

The rules to replace the Note services are very simple. If you provide an alternative implementation of the services then the default implementations will **not** be loaded.

### Custom Business Steps

It is very easy to add your own business steps to Fineract’s default steps:

1. Create a custom module (e. g. `custom/acme/steps`, follow the instructions on how to create a custom module)
2. Create a class that implements interface `org.apache.fineract.cob.COBBusinessStep`
3. Provide the custom database migration to add the necessary information about your business step in table `m_batch_business_steps`

```java
package org.apache.fineract.cob;

import org.apache.fineract.infrastructure.core.domain.AbstractPersistableCustom;

public interface COBBusinessStep<T extends AbstractPersistableCustom<Long>> {

    T execute(T input);

    String getEnumStyledName();

    String getHumanReadableName();
}
```

#### Business Step Implementation

```java
package com.acme.fineract.loan.cob;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.fineract.cob.loan.LoanCOBBusinessStep;
import org.apache.fineract.portfolio.loanaccount.domain.Loan;
import org.apache.fineract.portfolio.loanaccount.domain.LoanAccountDomainService;
import org.springframework.beans.factory.InitializingBean;
import org.springframework.stereotype.Component;

@Slf4j
@Component
@RequiredArgsConstructor
public class AcmeNoopBusinessStep implements LoanCOBBusinessStep, InitializingBean {

    private static final String ENUM_STYLED_NAME = "ACME_LOAN_NOOP";

    private static final String HUMAN_READABLE_NAME = "ACME Loan Noop";

    // NOTE: just to demonstrate that dependency injection is working
    private final LoanAccountDomainService loanAccountDomainService;

    @Override
    public void afterPropertiesSet() throws Exception {
        log.warn("Acme COB Loan: '{}'", getClass().getCanonicalName());
    }

    @Override
    public Loan execute(Loan input) {
        return input;
    }

    @Override
    public String getEnumStyledName() {
        return ENUM_STYLED_NAME;
    }

    @Override
    public String getHumanReadableName() {
        return HUMAN_READABLE_NAME;
    }
}
```

As you can see this implementation is very simple and doesn’t do much. There are some simple conventions though that you should follow implementing your own business steps:

1. Make sure the value returned by method `getEnumStyledName()` is unique; it’s a good idea to choose a prefix that reflects the name of your organization (in this example `ACME_`)
2. You have more freedom for the value returned by `getHumanReadableName()`, but it’s a good idea to keep this value as unique as possible

#### Business Step Database Migration

```xml
<databaseChangeLog xmlns="http://www.liquibase.org/xml/ns/dbchangelog"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   xsi:schemaLocation="http://www.liquibase.org/xml/ns/dbchangelog http://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-4.1.xsd">
    <changeSet author="acme" id="1">
        <insert tableName="m_batch_business_steps">
            <column name="job_name" value="LOAN_CLOSE_OF_BUSINESS"/>
            <column name="step_name" value="ACME_LOAN_NOOP"/>
            <column name="step_order" value="5"/>
        </insert>
    </changeSet>
</databaseChangeLog>
```

> [!NOTE]
> See also chapter about batch jobs in this documentation.

### Custom Loan Transaction Processors

Fineract has 7 built-in loan transaction processors:

1. `org.apache.fineract.portfolio.loanaccount.domain.transactionprocessor.impl.CreocoreLoanRepaymentScheduleTransactionProcessor`
2. `org.apache.fineract.portfolio.loanaccount.domain.transactionprocessor.impl.EarlyPaymentLoanRepaymentScheduleTransactionProcessor`
3. `org.apache.fineract.portfolio.loanaccount.domain.transactionprocessor.impl.FineractStyleLoanRepaymentScheduleTransactionProcessor`
4. `org.apache.fineract.portfolio.loanaccount.domain.transactionprocessor.impl.HeavensFamilyLoanRepaymentScheduleTransactionProcessor`
5. `org.apache.fineract.portfolio.loanaccount.domain.transactionprocessor.impl.InterestPrincipalPenaltyFeesOrderLoanRepaymentScheduleTransactionProcessor`
6. `org.apache.fineract.portfolio.loanaccount.domain.transactionprocessor.impl.PrincipalInterestPenaltyFeesOrderLoanRepaymentScheduleTransactionProcessor`
7. `org.apache.fineract.portfolio.loanaccount.domain.transactionprocessor.impl.RBILoanRepaymentScheduleTransactionProcessor`

```java
import org.apache.fineract.portfolio.loanaccount.service.LoanBalanceService;
import org.apache.fineract.portfolio.loanaccount.service.LoanChargeService;
import org.apache.fineract.portfolio.loanaccount.service.LoanMeetingCalendarService;
import org.apache.fineract.portfolio.loanaccount.service.ProgressiveLoanInterestRefundServiceImpl;
import org.apache.fineract.portfolio.loanaccount.service.schedule.LoanScheduleComponent;
import org.apache.fineract.portfolio.loanproduct.calc.EMICalculator;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Conditional;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Lazy;

@Configuration
public class LoanAccountAutoStarter {

    @Bean
    @Conditional(CreocoreLoanRepaymentScheduleTransactionProcessorCondition.class)
    public CreocoreLoanRepaymentScheduleTransactionProcessor creocoreLoanRepaymentScheduleTransactionProcessor(
            final ExternalIdFactory externalIdFactory, final LoanChargeValidator loanChargeValidator,
            final LoanBalanceService loanBalanceService) {
        return new CreocoreLoanRepaymentScheduleTransactionProcessor(externalIdFactory, loanChargeValidator, loanBalanceService);
    }

    @Bean
    @Conditional(EarlyRepaymentLoanRepaymentScheduleTransactionProcessorCondition.class)
    public EarlyPaymentLoanRepaymentScheduleTransactionProcessor earlyPaymentLoanRepaymentScheduleTransactionProcessor(
            final ExternalIdFactory externalIdFactory, final LoanChargeValidator loanChargeValidator,
            final LoanBalanceService loanBalanceService) {
        return new EarlyPaymentLoanRepaymentScheduleTransactionProcessor(externalIdFactory, loanChargeValidator, loanBalanceService);
    }

    @Bean
    @Conditional(MifosStandardLoanRepaymentScheduleTransactionProcessorCondition.class)
    public FineractStyleLoanRepaymentScheduleTransactionProcessor fineractStyleLoanRepaymentScheduleTransactionProcessor(
            final ExternalIdFactory externalIdFactory, final LoanChargeValidator loanChargeValidator,
            final LoanBalanceService loanBalanceService) {
        return new FineractStyleLoanRepaymentScheduleTransactionProcessor(externalIdFactory, loanChargeValidator, loanBalanceService);
    }

    @Bean
    @Conditional(HeavensFamilyLoanRepaymentScheduleTransactionProcessorCondition.class)
    public HeavensFamilyLoanRepaymentScheduleTransactionProcessor heavensFamilyLoanRepaymentScheduleTransactionProcessor(
            final ExternalIdFactory externalIdFactory, final LoanChargeValidator loanChargeValidator,
```

All default processor implementations are enabled by default, but can also be prevented from being loaded into memory by a simple configuration in `application.properties`. Use the environment variables you see below in your Kubernetes and Docker Compose deployments to override the default behavior.

```properties
fineract.tenant.description=${FINERACT_DEFAULT_TENANTDB_DESCRIPTION:Default Demo Tenant}
fineract.tenant.master-password=${FINERACT_DEFAULT_TENANTDB_MASTER_PASSWORD:fineract}
fineract.tenant.encrytion=${FINERACT_DEFAULT_TENANTDB_ENCRYPTION:"AES/CBC/PKCS5Padding"}

fineract.tenant.read-only-host=${FINERACT_DEFAULT_TENANTDB_RO_HOSTNAME:}
fineract.tenant.read-only-port=${FINERACT_DEFAULT_TENANTDB_RO_PORT:}
fineract.tenant.read-only-username=${FINERACT_DEFAULT_TENANTDB_RO_UID:}
```

#### Implement Processors

```java
package org.apache.fineract.portfolio.loanaccount.domain.transactionprocessor;

import java.time.LocalDate;
import java.util.List;
import java.util.Set;
import org.apache.fineract.organisation.monetary.domain.MonetaryCurrency;
import org.apache.fineract.organisation.monetary.domain.Money;
import org.apache.fineract.portfolio.loanaccount.domain.ChangedTransactionDetail;
import org.apache.fineract.portfolio.loanaccount.domain.LoanCharge;
import org.apache.fineract.portfolio.loanaccount.domain.LoanRepaymentScheduleInstallment;
import org.apache.fineract.portfolio.loanaccount.domain.LoanTransaction;

public interface LoanRepaymentScheduleTransactionProcessor {

    String getCode();

    String getName();

    boolean accept(String s);

    /**
     * Provides support for processing the latest transaction (which should be the latest transaction) against the loan
     * schedule.
     *
     * @return ChangedTransactionDetail
     */
    ChangedTransactionDetail processLatestTransaction(LoanTransaction loanTransaction, TransactionCtx ctx);

    /**
     * Provides support for passing all {@link LoanTransaction}'s so it will completely re-process the entire loan
     * schedule. This is required in cases where the {@link LoanTransaction} being processed is in the past and falls
     * before existing transactions or and adjustment is made to an existing in which case the entire loan schedule
     * needs to be re-processed.
     */
    ChangedTransactionDetail reprocessLoanTransactions(LocalDate disbursementDate, List<LoanTransaction> repaymentsOrWaivers,
            MonetaryCurrency currency, List<LoanRepaymentScheduleInstallment> repaymentScheduleInstallments, Set<LoanCharge> charges);

    Money handleRepaymentSchedule(List<LoanTransaction> transactionsPostDisbursement, MonetaryCurrency currency,
            List<LoanRepaymentScheduleInstallment> installments, Set<LoanCharge> loanCharges);

    /**
     * Used in interest recalculation to introduce new interest only installment.
     */
    boolean isInterestFirstRepaymentScheduleTransactionProcessor();
}
```

```java
package com.acme.fineract.loan.processor;

import org.apache.fineract.infrastructure.core.service.ExternalIdFactory;
import org.apache.fineract.portfolio.loanaccount.domain.transactionprocessor.impl.FineractStyleLoanRepaymentScheduleTransactionProcessor;
import org.apache.fineract.portfolio.loanaccount.serialization.LoanChargeValidator;
import org.apache.fineract.portfolio.loanaccount.service.LoanBalanceService;
import org.springframework.stereotype.Component;

@Component
public class AcmeLoanRepaymentScheduleTransactionProcessor extends FineractStyleLoanRepaymentScheduleTransactionProcessor {

    public static final String STRATEGY_CODE = "acme-standard-strategy";

    public static final String STRATEGY_NAME = "ACME Corp.: standard loan transaction processing strategy";

    public AcmeLoanRepaymentScheduleTransactionProcessor(final ExternalIdFactory externalIdFactory,
            final LoanChargeValidator loanChargeValidator, final LoanBalanceService loanBalanceService) {
        super(externalIdFactory, loanChargeValidator, loanBalanceService);
    }

    @Override
    public String getCode() {
        return STRATEGY_CODE;
    }

    @Override
    public String getName() {
        return STRATEGY_NAME;
    }

}
```

The example implementation doesn’t do much. We are just overriding one of the default processor implementations `org.apache.fineract.portfolio.loanaccount.domain.transactionprocessor.impl.FineractStyleLoanRepaymentScheduleTransactionProcessor` and give the custom processor it’s own lookup code and name (descriptive text for display in UIs, e. g. when configuring a loan product). As usual it is a good idea to follow some simple conventions:

1. Make sure the value returned by `getCode()` is unique. Prefixing it with characters that reflect your organization name (here `acme-`) is a good idea.
2. You have more freedom for the descriptive test returned by `getName()`, but it is still a good idea to keep the value unique to avoid confusion.

##### MethodgetCode()

Lookup value that is used to pick a loan transaction processor (see processor factory).

##### MethodgetName()

Descriptive text about the loan transaction processor that is mostly used in user interfaces.

##### MethodhandleTransaction()

TBD

##### MethodhandleWriteOff()

TBD

##### MethodhandleRepaymentSchedule()

TBD

##### MethodisInterestFirstRepaymentScheduleTransactionProcessor()

TBD

##### MethodhandleRefund()

TBD

##### MethodhandleChargeback()

TBD

##### MethodprocessTransactionsFromDerivedFields()

TBD

#### Override Processor Factory

The processor factory has no reference to any specific implementation of the loan transaction processor interface. All available implementations will be injected here (internal default and custom implementations). Processor instances can be looked up via method `determineProcessor()`. You can pass either the code of the processor or the processor’s name to look it up. If a matching processor can’t be found then the factory function will either return the default instance or fails with an exception depending on the configuration in `application.properties`.

> [!IMPORTANT]
> It is preferable to use the processor code to lookup processor instances. Lookups via processor names are only done in the import service via Excel sheets (should be fixed).

```java
package org.apache.fineract.portfolio.loanaccount.domain;

import java.util.List;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import org.apache.fineract.portfolio.loanaccount.domain.transactionprocessor.LoanRepaymentScheduleTransactionProcessor;
import org.apache.fineract.portfolio.loanaccount.exception.LoanTransactionProcessingStrategyNotFoundException;
import org.apache.fineract.portfolio.loanproduct.data.TransactionProcessingStrategyData;
import org.springframework.beans.factory.annotation.Value;

@RequiredArgsConstructor
public class LoanRepaymentScheduleTransactionProcessorFactory {

    private final LoanRepaymentScheduleTransactionProcessor defaultLoanRepaymentScheduleTransactionProcessor;

    private final List<LoanRepaymentScheduleTransactionProcessor> processors;

    @Value("${fineract.loan.transactionprocessor.error-not-found-fail}")
    private Boolean errorNotFoundFail;

    public LoanRepaymentScheduleTransactionProcessor determineProcessor(final String transactionProcessingStrategy) {

        Optional<LoanRepaymentScheduleTransactionProcessor> processor = processors.stream()
                .filter(p -> p.accept(transactionProcessingStrategy)).findFirst();

        if (processor.isEmpty() && Boolean.TRUE.equals(errorNotFoundFail)) {
            throw new LoanTransactionProcessingStrategyNotFoundException(transactionProcessingStrategy);
        } else {
            return processor.orElse(defaultLoanRepaymentScheduleTransactionProcessor);
        }
    }

    public List<TransactionProcessingStrategyData> getStrategies() {
        return processors.stream().map(p -> new TransactionProcessingStrategyData(null, p.getCode(), p.getName())).toList();
    }
}
```

This is the default factory auto-configuration.

```java
            final LoanBalanceService loanBalanceService) {
        return new HeavensFamilyLoanRepaymentScheduleTransactionProcessor(externalIdFactory, loanChargeValidator, loanBalanceService);
    }

    @Bean
    @Conditional(InterestPrincipalPenaltiesFeesLoanRepaymentScheduleTransactionProcessorCondition.class)
    public InterestPrincipalPenaltyFeesOrderLoanRepaymentScheduleTransactionProcessor interestPrincipalPenaltyFeesOrderLoanRepaymentScheduleTransactionProcessor(
```

If you need then you can override this, e.g. because you want to set a different default processor then you can do so in your custom module’s auto-configuration.

```java
    public LoanRepaymentScheduleTransactionProcessorFactory loanRepaymentScheduleTransactionProcessorFactory(
            AcmeLoanRepaymentScheduleTransactionProcessor defaultLoanRepaymentScheduleTransactionProcessor,
            List<LoanRepaymentScheduleTransactionProcessor> processors) {
        return new LoanRepaymentScheduleTransactionProcessorFactory(defaultLoanRepaymentScheduleTransactionProcessor, processors);
    }
}
```

```properties
fineract.tenant.read-only-password=${FINERACT_DEFAULT_TENANTDB_RO_PWD:}
```

### Custom Batch Jobs

Fineract provides extension points to define custom batch jobs using module system. Using this approach custom batch jobs can be defined and configured along with Fineract’s default batch jobs to extend or customize batch processing.

The batch jobs in Fineract are implemented using [Spring Batch](https://docs.spring.io/spring-batch/docs/current/reference/html/). In addition to the Spring Batch ecosystem, automatic scheduling is done by [Quartz Scheduler](http://www.quartz-scheduler.org/) but it’s also possible to trigger batch jobs via regular APIs.

For defining custom job:

1. Create custom module (e. g. `custom/acme/loan/job`), follow the instructions on how to create a custom module.
2. Create job configuration to register job, job steps, tasklet with job builder factory. (e. g. `com.acme.fineract.loan.job.AcmeNoopJobConfiguration`)
3. Create tasklet for job execution functionality. (e.g. `com.acme.fineract.loan.job.AcmeNoopJobTasklet`)
4. Provide the custom database migration to add necessary information about your job in table `job`. (e.g. `custom/acme/loan/job/src/main/resources/db/custom-changelog/0001_acme_loan_job.xml`)
5. New job name should be registered along with default jobs so that it can be scheduled at startup. For registering job name with Fineract job scheduler, create an enum with job name details (e.g. `com.acme.fineract.loan.job.AcmeJobName`) and a job name provider configuration which is accessed by Fineract job scheduler at startup to retrieve job name (e.g. `com.acme.fineract.loan.job.AcmeJobNameConfig`).

#### Job Configuration

```java
package com.acme.fineract.loan.job;

import lombok.RequiredArgsConstructor;
import org.springframework.batch.core.job.Job;
import org.springframework.batch.core.job.builder.JobBuilder;
import org.springframework.batch.core.repository.JobRepository;
import org.springframework.batch.core.step.Step;
import org.springframework.batch.core.step.builder.StepBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.transaction.PlatformTransactionManager;

@Configuration
@RequiredArgsConstructor
public class AcmeNoopJobConfiguration {

    private final JobRepository jobRepository;
    private final PlatformTransactionManager transactionManager;
    private final AcmeNoopJobTasklet tasklet;

    @Bean
    protected Step acmeNoopJobStep() {
        return new StepBuilder(AcmeJobName.ACME_NOOP_JOB.name(), jobRepository).tasklet(tasklet, transactionManager).build();
    }

    @Bean
    public Job acmeNoopJob() {
        return new JobBuilder(AcmeJobName.ACME_NOOP_JOB.name(), jobRepository).start(acmeNoopJobStep()).build();
    }

}
```

#### Tasklet Definition

```java
package com.acme.fineract.loan.job;

import lombok.extern.slf4j.Slf4j;
import org.springframework.batch.core.scope.context.ChunkContext;
import org.springframework.batch.core.step.StepContribution;
import org.springframework.batch.core.step.tasklet.Tasklet;
import org.springframework.batch.infrastructure.repeat.RepeatStatus;
import org.springframework.stereotype.Component;

@Slf4j
@Component
public class AcmeNoopJobTasklet implements Tasklet {

    @Override
    public RepeatStatus execute(StepContribution contribution, ChunkContext chunkContext) throws Exception {
        log.info("Acme custom job execution");
        return RepeatStatus.FINISHED;
    }
}
```

#### Database Migration Script for Job

```xml
<databaseChangeLog xmlns="http://www.liquibase.org/xml/ns/dbchangelog"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   xsi:schemaLocation="http://www.liquibase.org/xml/ns/dbchangelog http://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-4.1.xsd">
    <changeSet author="acme" id="1">
        <insert tableName="job">
            <column name="name" value="Acme Noop Job"/>
            <column name="display_name" value="Acme Noop Job"/>
            <column name="cron_expression" value="0 1 0 1/1 * ? *"/>
            <column name="create_time" valueDate="${current_datetime}"/>
            <column name="task_priority" valueNumeric="5"/>
            <column name="group_name"/>
            <column name="previous_run_start_time"/>
            <column name="job_key" value="Acme Noop Job _ DEFAULT"/>
            <column name="initializing_errorlog"/>
            <column name="is_active" valueBoolean="false"/>
            <column name="currently_running" valueBoolean="false"/>
            <column name="updates_allowed" valueBoolean="true"/>
            <column name="scheduler_group" valueNumeric="0"/>
            <column name="is_misfired" valueBoolean="false"/>
            <column name="node_id" valueNumeric="1"/>
            <column name="is_mismatched_job" valueBoolean="true"/>
        </insert>
    </changeSet>
    <changeSet author="acme" id="2">
        <update tableName="job">
            <column name="short_name" value="ACM_NOOP"/>
            <where>name='Acme Noop Job'</where>
        </update>
    </changeSet>
</databaseChangeLog>
```

#### Job Name Configuration

```java
package com.acme.fineract.loan.job;

public enum AcmeJobName {

    ACME_NOOP_JOB("Acme Noop Job"); //

    private final String name;

    AcmeJobName(final String name) {
        this.name = name;
    }

    @Override
    public String toString() {
        return this.name;
    }
}
```

```java
package com.acme.fineract.loan.job;

import java.util.List;
import org.apache.fineract.infrastructure.jobs.service.jobname.JobNameData;
import org.apache.fineract.infrastructure.jobs.service.jobname.JobNameProvider;
import org.apache.fineract.infrastructure.jobs.service.jobname.SimpleJobNameProvider;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class AcmeJobNameConfig {

    @Bean
    public JobNameProvider acmeJobNameProvider() {
        return new SimpleJobNameProvider(List.of(new JobNameData(AcmeJobName.ACME_NOOP_JOB.name(), AcmeJobName.ACME_NOOP_JOB.toString())));
    }
}
```

#### Gradle Build Files

Please make sure that your module libraries have proper `build.gradle` and `dependencies.gradle` files:

```
build.gradle
```

```
dependencies.gradle
```

#### Deployment

Custom modules can be deployed using docker image. See chapter about deploying custom modules in this documentation.

```bash
./gradlew :custom:docker:jibDockerBuild
```

> [!NOTE]
> See also chapter about batch jobs in this documentation.

### Custom Database Migration

If database migrations are needed as part of your customizations then you can add your own migration scripts. This is again based on conventions:

1. Create folders `db/custom-changelog` in one of your `resources` folders; we recommend using the resources folder in your starter library, but actually any of your custom libs will do.
2. Under `db/custom-changelog` create an XML changelog file, e. g. `changelog-acme-note.xml`; you are free to choose a name for this file, but we recommend being consistent to avoid classpath conflicts.
3. Under `db/custom-changelog` create a folder `parts` for your specific changelogs

![Diagram](data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0nMS4wJyBlbmNvZGluZz0nVVRGLTgnIHN0YW5kYWxvbmU9J25vJz8+PHN2ZyBjb250ZW50U3R5bGVUeXBlPSd0ZXh0L2NzcycgaGVpZ2h0PSczMjFweCcgcHJlc2VydmVBc3BlY3RSYXRpbz0nbm9uZScgc3R5bGU9J3dpZHRoOjUwMHB4O2hlaWdodDozMjFweDtiYWNrZ3JvdW5kOiNGRkZGRkY7JyB2ZXJzaW9uPScxLjEnIHZpZXdCb3g9JzAgMCA1MDAgMzIxJyB3aWR0aD0nNTAwcHgnIHhtbG5zOnhsaW5rPSdodHRwOi8vd3d3LnczLm9yZy8xOTk5L3hsaW5rJyB4bWxucz0naHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmcnIHpvb21BbmRQYW49J21hZ25pZnknPjxkZWZzLz48Zz48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSc0MScgeD0nMTYnIHk9JzE4LjgyODEnPmN1c3RvbTwvdGV4dD48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPSczMScgeD0nMjYnIHk9JzM1LjE3MjInPmFjbWU8L3RleHQ+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMjUnIHg9JzM2JyB5PSc1MS41MTYzJz5ub3RlPC90ZXh0Pjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEyJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzM4JyB4PSc0NicgeT0nNjcuODYwNCc+c3RhcnRlcjwvdGV4dD48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxNycgeD0nNTYnIHk9Jzg0LjIwNDUnPnNyYzwvdGV4dD48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScyOCcgeD0nNjYnIHk9JzEwMC41NDg3Jz5tYWluPC90ZXh0Pjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEyJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzIzJyB4PSc3NicgeT0nMTE2Ljg5MjgnPmphdmE8L3RleHQ+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nMTczJyB4PSc4NicgeT0nMTMzLjIzNjknPmNvbS5hY21lLmZpbmVyYWN0Lm5vdGUuc3RhcnRlcjwvdGV4dD48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxODcnIHg9Jzk2JyB5PScxNDkuNTgxJz5BY21lTm90ZUF1dG9Db25maWd1cmF0aW9uLmphdmE8L3RleHQ+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nNTYnIHg9JzU2JyB5PScxNjUuOTI1MSc+cmVzb3VyY2VzPC90ZXh0Pjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEyJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzE0JyB4PSc2NicgeT0nMTgyLjI2OTInPmRiPC90ZXh0Pjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEyJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzEwMycgeD0nNzYnIHk9JzE5OC42MTMzJz5jdXN0b20tY2hhbmdlbG9nPC90ZXh0Pjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEyJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzI5JyB4PSc4NicgeT0nMjE0Ljk1NzUnPnBhcnRzPC90ZXh0Pjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEyJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzE1MicgeD0nOTYnIHk9JzIzMS4zMDE2Jz4wMDAxX2FjbWVfbm90ZV9pbml0aWFsLnhtbDwvdGV4dD48dGV4dCBmaWxsPScjMDAwMDAwJyBmb250LWZhbWlseT0nc2Fucy1zZXJpZicgZm9udC1zaXplPScxMicgbGVuZ3RoQWRqdXN0PSdzcGFjaW5nJyB0ZXh0TGVuZ3RoPScxNDUnIHg9Jzg2JyB5PScyNDcuNjQ1Nyc+Y2hhbmdlbG9nLWFjbWUtbm90ZS54bWw8L3RleHQ+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nNTYnIHg9JzY2JyB5PScyNjMuOTg5OCc+TUVUQS1JTkY8L3RleHQ+PHRleHQgZmlsbD0nIzAwMDAwMCcgZm9udC1mYW1pbHk9J3NhbnMtc2VyaWYnIGZvbnQtc2l6ZT0nMTInIGxlbmd0aEFkanVzdD0nc3BhY2luZycgdGV4dExlbmd0aD0nNDE3JyB4PSc3NicgeT0nMjgwLjMzMzknPnNwcmluZy9vcmcuc3ByaW5nZnJhbWV3b3JrLmJvb3QuYXV0b2NvbmZpZ3VyZS5BdXRvQ29uZmlndXJhdGlvbi5pbXBvcnRzPC90ZXh0Pjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEyJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzY2JyB4PSc1NicgeT0nMjk2LjY3OCc+YnVpbGQuZ3JhZGxlPC90ZXh0Pjx0ZXh0IGZpbGw9JyMwMDAwMDAnIGZvbnQtZmFtaWx5PSdzYW5zLXNlcmlmJyBmb250LXNpemU9JzEyJyBsZW5ndGhBZGp1c3Q9J3NwYWNpbmcnIHRleHRMZW5ndGg9JzExNycgeD0nNTYnIHk9JzMxMy4wMjIxJz5kZXBlbmRlbmNpZXMuZ3JhZGxlPC90ZXh0PjxyZWN0IGZpbGw9J25vbmUnIGhlaWdodD0nMicgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB3aWR0aD0nMicgeD0nOScgeT0nMTMuMTcyMScvPjxyZWN0IGZpbGw9J25vbmUnIGhlaWdodD0nMicgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB3aWR0aD0nMicgeD0nMTknIHk9JzI5LjUxNjInLz48bGluZSBzdHlsZT0nc3Ryb2tlOiM4ODg4ODg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPScxMCcgeDI9JzEwJyB5MT0nMTYuMTcyMScgeTI9JzMwLjUxNjInLz48bGluZSBzdHlsZT0nc3Ryb2tlOiM4ODg4ODg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPScxMCcgeDI9JzE4JyB5MT0nMzAuNTE2MicgeTI9JzMwLjUxNjInLz48cmVjdCBmaWxsPSdub25lJyBoZWlnaHQ9JzInIHN0eWxlPSdzdHJva2U6Izg4ODg4ODtzdHJva2Utd2lkdGg6MS4wOycgd2lkdGg9JzInIHg9JzI5JyB5PSc0NS44NjAzJy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nMjAnIHgyPScyMCcgeTE9JzMyLjUxNjInIHkyPSc0Ni44NjAzJy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nMjAnIHgyPScyOCcgeTE9JzQ2Ljg2MDMnIHkyPSc0Ni44NjAzJy8+PHJlY3QgZmlsbD0nbm9uZScgaGVpZ2h0PScyJyBzdHlsZT0nc3Ryb2tlOiM4ODg4ODg7c3Ryb2tlLXdpZHRoOjEuMDsnIHdpZHRoPScyJyB4PSczOScgeT0nNjIuMjA0NCcvPjxsaW5lIHN0eWxlPSdzdHJva2U6Izg4ODg4ODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzMwJyB4Mj0nMzAnIHkxPSc0OC44NjAzJyB5Mj0nNjMuMjA0NCcvPjxsaW5lIHN0eWxlPSdzdHJva2U6Izg4ODg4ODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzMwJyB4Mj0nMzgnIHkxPSc2My4yMDQ0JyB5Mj0nNjMuMjA0NCcvPjxyZWN0IGZpbGw9J25vbmUnIGhlaWdodD0nMicgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB3aWR0aD0nMicgeD0nNDknIHk9Jzc4LjU0ODUnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiM4ODg4ODg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSc0MCcgeDI9JzQwJyB5MT0nNjUuMjA0NCcgeTI9Jzc5LjU0ODUnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiM4ODg4ODg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSc0MCcgeDI9JzQ4JyB5MT0nNzkuNTQ4NScgeTI9Jzc5LjU0ODUnLz48cmVjdCBmaWxsPSdub25lJyBoZWlnaHQ9JzInIHN0eWxlPSdzdHJva2U6Izg4ODg4ODtzdHJva2Utd2lkdGg6MS4wOycgd2lkdGg9JzInIHg9JzU5JyB5PSc5NC44OTI2Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nNTAnIHgyPSc1MCcgeTE9JzgxLjU0ODUnIHkyPSc5NS44OTI2Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nNTAnIHgyPSc1OCcgeTE9Jzk1Ljg5MjYnIHkyPSc5NS44OTI2Jy8+PHJlY3QgZmlsbD0nbm9uZScgaGVpZ2h0PScyJyBzdHlsZT0nc3Ryb2tlOiM4ODg4ODg7c3Ryb2tlLXdpZHRoOjEuMDsnIHdpZHRoPScyJyB4PSc2OScgeT0nMTExLjIzNjcnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiM4ODg4ODg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSc2MCcgeDI9JzYwJyB5MT0nOTcuODkyNicgeTI9JzExMi4yMzY3Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nNjAnIHgyPSc2OCcgeTE9JzExMi4yMzY3JyB5Mj0nMTEyLjIzNjcnLz48cmVjdCBmaWxsPSdub25lJyBoZWlnaHQ9JzInIHN0eWxlPSdzdHJva2U6Izg4ODg4ODtzdHJva2Utd2lkdGg6MS4wOycgd2lkdGg9JzInIHg9Jzc5JyB5PScxMjcuNTgwOScvPjxsaW5lIHN0eWxlPSdzdHJva2U6Izg4ODg4ODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzcwJyB4Mj0nNzAnIHkxPScxMTQuMjM2NycgeTI9JzEyOC41ODA5Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nNzAnIHgyPSc3OCcgeTE9JzEyOC41ODA5JyB5Mj0nMTI4LjU4MDknLz48bGluZSBzdHlsZT0nc3Ryb2tlOiM4ODg4ODg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSc4MCcgeDI9JzgwJyB5MT0nMTMwLjU4MDknIHkyPScxNDQuOTI1Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nODAnIHgyPSc4OCcgeTE9JzE0NC45MjUnIHkyPScxNDQuOTI1Jy8+PHJlY3QgZmlsbD0nbm9uZScgaGVpZ2h0PScyJyBzdHlsZT0nc3Ryb2tlOiM4ODg4ODg7c3Ryb2tlLXdpZHRoOjEuMDsnIHdpZHRoPScyJyB4PSc0OScgeT0nMTYwLjI2OTEnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiM4ODg4ODg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSc0MCcgeDI9JzQwJyB5MT0nNjUuMjA0NCcgeTI9JzE2MS4yNjkxJy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nNDAnIHgyPSc0OCcgeTE9JzE2MS4yNjkxJyB5Mj0nMTYxLjI2OTEnLz48cmVjdCBmaWxsPSdub25lJyBoZWlnaHQ9JzInIHN0eWxlPSdzdHJva2U6Izg4ODg4ODtzdHJva2Utd2lkdGg6MS4wOycgd2lkdGg9JzInIHg9JzU5JyB5PScxNzYuNjEzMicvPjxsaW5lIHN0eWxlPSdzdHJva2U6Izg4ODg4ODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzUwJyB4Mj0nNTAnIHkxPScxNjMuMjY5MScgeTI9JzE3Ny42MTMyJy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nNTAnIHgyPSc1OCcgeTE9JzE3Ny42MTMyJyB5Mj0nMTc3LjYxMzInLz48cmVjdCBmaWxsPSdub25lJyBoZWlnaHQ9JzInIHN0eWxlPSdzdHJva2U6Izg4ODg4ODtzdHJva2Utd2lkdGg6MS4wOycgd2lkdGg9JzInIHg9JzY5JyB5PScxOTIuOTU3MycvPjxsaW5lIHN0eWxlPSdzdHJva2U6Izg4ODg4ODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzYwJyB4Mj0nNjAnIHkxPScxNzkuNjEzMicgeTI9JzE5My45NTczJy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nNjAnIHgyPSc2OCcgeTE9JzE5My45NTczJyB5Mj0nMTkzLjk1NzMnLz48cmVjdCBmaWxsPSdub25lJyBoZWlnaHQ9JzInIHN0eWxlPSdzdHJva2U6Izg4ODg4ODtzdHJva2Utd2lkdGg6MS4wOycgd2lkdGg9JzInIHg9Jzc5JyB5PScyMDkuMzAxNCcvPjxsaW5lIHN0eWxlPSdzdHJva2U6Izg4ODg4ODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzcwJyB4Mj0nNzAnIHkxPScxOTUuOTU3MycgeTI9JzIxMC4zMDE0Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nNzAnIHgyPSc3OCcgeTE9JzIxMC4zMDE0JyB5Mj0nMjEwLjMwMTQnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiM4ODg4ODg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSc4MCcgeDI9JzgwJyB5MT0nMjEyLjMwMTQnIHkyPScyMjYuNjQ1NScvPjxsaW5lIHN0eWxlPSdzdHJva2U6Izg4ODg4ODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzgwJyB4Mj0nODgnIHkxPScyMjYuNjQ1NScgeTI9JzIyNi42NDU1Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nNzAnIHgyPSc3MCcgeTE9JzE5NS45NTczJyB5Mj0nMjQyLjk4OTcnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiM4ODg4ODg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSc3MCcgeDI9Jzc4JyB5MT0nMjQyLjk4OTcnIHkyPScyNDIuOTg5NycvPjxyZWN0IGZpbGw9J25vbmUnIGhlaWdodD0nMicgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB3aWR0aD0nMicgeD0nNTknIHk9JzI1OC4zMzM4Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nNTAnIHgyPSc1MCcgeTE9JzE2My4yNjkxJyB5Mj0nMjU5LjMzMzgnLz48bGluZSBzdHlsZT0nc3Ryb2tlOiM4ODg4ODg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSc1MCcgeDI9JzU4JyB5MT0nMjU5LjMzMzgnIHkyPScyNTkuMzMzOCcvPjxsaW5lIHN0eWxlPSdzdHJva2U6Izg4ODg4ODtzdHJva2Utd2lkdGg6MS4wOycgeDE9JzYwJyB4Mj0nNjAnIHkxPScyNjEuMzMzOCcgeTI9JzI3NS42Nzc5Jy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nNjAnIHgyPSc2OCcgeTE9JzI3NS42Nzc5JyB5Mj0nMjc1LjY3NzknLz48bGluZSBzdHlsZT0nc3Ryb2tlOiM4ODg4ODg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSc0MCcgeDI9JzQwJyB5MT0nNjUuMjA0NCcgeTI9JzI5Mi4wMjInLz48bGluZSBzdHlsZT0nc3Ryb2tlOiM4ODg4ODg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSc0MCcgeDI9JzQ4JyB5MT0nMjkyLjAyMicgeTI9JzI5Mi4wMjInLz48bGluZSBzdHlsZT0nc3Ryb2tlOiM4ODg4ODg7c3Ryb2tlLXdpZHRoOjEuMDsnIHgxPSc0MCcgeDI9JzQwJyB5MT0nNjUuMjA0NCcgeTI9JzMwOC4zNjYxJy8+PGxpbmUgc3R5bGU9J3N0cm9rZTojODg4ODg4O3N0cm9rZS13aWR0aDoxLjA7JyB4MT0nNDAnIHgyPSc0OCcgeTE9JzMwOC4zNjYxJyB5Mj0nMzA4LjM2NjEnLz48L2c+PC9zdmc+)

And here an example migration script:

```xml
<databaseChangeLog xmlns="http://www.liquibase.org/xml/ns/dbchangelog"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   xsi:schemaLocation="http://www.liquibase.org/xml/ns/dbchangelog http://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-4.1.xsd">
    <changeSet author="acme" id="1">
        <createTable tableName="acme_note_dummy">
            <column autoIncrement="true" name="id" type="BIGINT">
                <constraints nullable="false" primaryKey="true"/>
            </column>
            <column name="name" type="VARCHAR(100)">
                <constraints unique="true"/>
            </column>
            <column name="description" type="VARCHAR(500)"/>
        </createTable>
    </changeSet>
</databaseChangeLog>
```

> [!IMPORTANT]
> By default, custom database migration changelogs are executed in context `tenant_db`. That makes sure your changes will be applied to the tenant database (read: main database and not the tenant store database). In theory you could also target the tenant configuration database, but it’s not recommended to do that.

### Deploying Custom Modules

Custom modules (better: the JAR files) only need to be dropped in Fineract’s `libs` folder if you run Fineract from the Spring Boot JAR file. Dynamic loading of external JARs is provided since Fineract version 1.5.0. For your convenience we’ve created a separate Docker image module that automatically includes your custom modules (see `custom/docker`). You can build this Docker image with

```bash
./gradlew :custom:docker:jibDockerBuild
```

The Docker image with included custom modules is called `fineract-custom`.

> [!NOTE]
> We’ll provide soon a way to customize the Docker image parameters (image name, JVM implementation, JVM args, ports etc.).

### Outlook

If this **proof of concept** is accepted we could prepare more of Fineract’s internal services to be replaceable. This approach works already very well even if we don’t have proper JAR libraries published on Maven Central. It’s an important goal to separate customized code from Fineract’s internals to have soon real modules.