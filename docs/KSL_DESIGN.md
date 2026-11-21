# KSL design

CareLoop can offer Kenyan Sign Language as a third language on the patient card and in the channel opening. The avatar plays an approved recording of one fixed line. It does not turn free text into a sign, and it does not read the camera.

## Where it sits

The patient card is `frontend/src/app/enter/EnterFlow.tsx`. English and Kiswahili keep the spoken guide. Kenyan Sign Language calls `POST /api/v1/ksl/talk` and shows captions plus, when no approved clip exists, a labelled test motion.

Telegram can attach a rendered video of an approved clip. If that video is missing, the reply is captions, icon names, and a human task. USSD and SMS stay text. They cannot show a signer.

## Playback

`frontend/src/ksl/engine.js` plays frames from a clock, not from a render tick. A new clip blends for 200 ms. Speed is 0.75 or 1. Pause, replay, and step-through are supported. Hands and face are not smoothed. While a clip is signing, procedural face, head, gaze, and torso stay off.

Reduced motion does not freeze a sign halfway. It starts in step-through and keeps the caption.

Idle, attentive, signing, holding, and returning are states in that same file. There is no measured phone frame rate in this build. None is claimed.

## What is on screen

The rig file `assets/ksl/rig/guide.gltf` is a list of joint names. It is not a scanned person. The card draws a coloured arm only for the test wave, under the label `PLACEHOLDER MOTION: NOT KSL`.

React Three Fiber was the planned renderer because the card is already React. It is not installed. There is no reviewed mesh to put in a scene. Four appearance presets (coast, highland, city, clinic) are colours, not portraits.

## Fallback

Avatar, then a rendered video, then captions and icons, then a person. `backend/app/modules/ksl/fallback.py` and `chooseFallback` in the engine follow that order.

## Safety

Worse, unclear, need-help, and can't-go still open a human task. The guide does not say someone is fine. A missed KSL check-in is raised on the first miss, not the third. The worklist action is text or video, a home visit with a KSL-aware community health promoter, or booking an interpreter. A phone call is not the default.

The guided call is taps. The camera stays off. The recogniser interface has a simulator for tests and a disabled recogniser on the API. The product text is "Recognition not enabled in this build."
