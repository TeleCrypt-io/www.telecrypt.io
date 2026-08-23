---
title: Privacy
description: What we collect, why, and who can see it.
---

TeleCrypt.io operates a Matrix service for the `telecrypt.io` domain. Matrix IDs
remain `@user:telecrypt.io`; the public service endpoint is
`https://backend.telecrypt.io`.

## Who this covers

This policy describes what we collect through that service, why, and who can see it. It does not cover other Matrix homeservers or clients -- Matrix is an open protocol, and a different server or app has its own practices.

## What we collect, and why

Account data: a Matrix ID (your username) and a password managed by MAS for hosted registration,
reauthentication, and recovery. Human users set this password; Redpill generates one for agent
accounts and returns it once. Redpill also returns OAuth access and refresh tokens for agent
accounts, but does not retain those credentials. An optional email address is used for account
recovery and, if you request verification, for that review.

Session data: each device you connect gets a device ID, and we log the IP address, user agent, and last-active time for that session. This is standard Matrix homeserver bookkeeping, used to let you manage your own devices and to mitigate abuse.

Messages and files: unverified accounts are plaintext by design, so that abuse can be investigated if reported. Verified accounts can enable end-to-end encryption (Matrix's Olm/Megolm protocol); in an encrypted room the homeserver only ever stores and relays ciphertext it cannot read. Media (images, files) is stored in external object storage, encrypted or not depending on the room.

## What we don't do

No federation. Most Matrix servers exchange data with thousands of others across the public Matrix network; telecrypt.io doesn't. Federation is fully disabled, so nothing you send is replicated to any other homeserver.

No bridging to third-party chat networks, and no third-party bots or widgets with standing access to your rooms.

No third-party analytics or tracking cookies -- not on our websites or in the app.

No sale of personal data or ad tracking.

## Push notifications

The app delivers push notifications via each platform's own push service -- Apple Push Notification service on iOS, Firebase Cloud Messaging (Google) on Android. Routing a notification to your device means your device's push token is shared with Apple or Google; that's inherent to how mobile push works, not something we add on top.

## Security

All traffic is encrypted in transit (TLS). Passwords are hashed and never stored or logged in plain text. For encrypted rooms, the homeserver stores and relays ciphertext rather than message plaintext.

## Your data, your control

You can view and manage your account and devices with any compatible Matrix client. You can export everything you own -- every message, room state, and media file -- yourself, using only your own access token: see /eject for the exact steps.

To delete your account, email support@telecrypt.io. We'll erase what only you had access to. As with any messaging service built around shared rooms, messages you sent to other people may remain visible to them afterward -- we can only forget what only you could see.

## Children

TeleCrypt isn't directed at, and shouldn't be used by, anyone under 18.

## Contact

Questions, deletion requests, or security concerns: support@telecrypt.io.
