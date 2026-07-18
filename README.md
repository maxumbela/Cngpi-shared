# CNGPI Student Portal

### Class routines, books, CGPA — built for polytechnic students.

<p align="center">
  <img src="https://img.shields.io/badge/Portal-Student-6366F1?style=for-the-badge" alt="Student Portal" />
  <img src="https://img.shields.io/badge/Hosting-Firebase-FFCA28?style=for-the-badge&logo=firebase&logoColor=black" alt="Firebase" />
  <img src="https://img.shields.io/badge/Stack-HTML%20%7C%20CSS%20%7C%20JS-0EA5E9?style=for-the-badge" alt="Stack" />
  <img src="https://img.shields.io/badge/Backend-Firestore-FF6F00?style=for-the-badge&logo=firebase&logoColor=white" alt="Firestore" />
</p>

<p align="center">
  <strong>CNGPI</strong> — Chapainawabganj Polytechnic Institute student web portal
</p>

---

A mobile-first education portal for CNGPI students. Browse class routines by group, check book lists, calculate CGPA, and manage content from a dedicated admin console — all on **Firebase Hosting + Firestore**.

<br>

## Features

| Module | Status | Description |
|---|---|---|
| **Dashboard** | Live | Mobile-style home with greeting, group pill, and feature cards |
| **Routine** | Live | Group-based class timetable; swipeable week view |
| **Books** | Live | Semester polytechnic textbook list (`/books`) |
| **CGPA Calculator** | Live | BTEB-style grade calculator (`/calculator`) |
| **Admin Console** | Live | Manage routines for groups (`/admin`) |
| **Notice** | Coming soon | Campus notices |
| **Result** | Coming soon | Exam results |

### Student experience
- Group code selection (e.g. `CST 3/1`, `ET 3/1`) with Firestore-backed suggestions  
- Clean smartphone-style UI (Inter + Outfit)  
- Lucide icons, toast notifications, offline fallback group codes  
- Export-friendly routine layout (html2canvas support on main portal)  

<br>

## Routes

| Path | File | Purpose |
|---|---|---|
| `/` | `public/index.html` | Student dashboard & routine entry |
| `/routine` | `public/routine.html` | Standalone routine page |
| `/books` | `public/books.html` | Book list |
| `/calculator` | `public/calculator.html` | CGPA calculator |
| `/admin` | `public/admin.html` | Admin console |

<br>

## Tech stack

```text
Frontend     HTML · CSS · Vanilla JavaScript
Fonts        Inter · Outfit
Icons        Lucide
Extras       html2canvas (routine export)
Backend      Cloud Firestore (compat SDK 10.8)
Auth         Firebase Auth (email/password for admin)
Hosting      Firebase Hosting (target: cngpi)
Project ID   cngpi-edu
```

No bundler or framework required — static files under `public/`.

<br>

## Project structure

```text
CNGPI-web/
├── public/                      # Firebase Hosting root
│   ├── index.html               # Student portal home
│   ├── routine.html             # Class routine
│   ├── books.html               # Book list
│   ├── calculator.html          # CGPA calculator
│   ├── admin.html               # Admin dashboard
│   ├── app.js                   # Portal logic + Firebase init
│   ├── style.css                # Shared styles
│   ├── lucide.min.js            # Local icon fallback
│   └── assets/                  # Icons & images
├── firebase.json                # Hosting rewrites + Firestore config
├── firestore.rules              # Security rules
├── firestore.indexes.json       # Indexes
├── .firebaserc                  # Project + hosting target
├── generate_routine.js          # Utility script for routines
└── README.md
```

<br>

## Getting started

### Prerequisites
- [Node.js](https://nodejs.org/)
- Firebase CLI with access to project `cngpi-edu`

### Install & login

```bash
npm install -g firebase-tools
firebase login
firebase use cngpi-edu
```

### Local preview

```bash
firebase serve --only hosting
```

Open the local URL (usually `http://localhost:5000`).

### Deploy

```bash
# Hosting only
firebase deploy --only hosting:cngpi

# Rules + indexes (when changed)
firebase deploy --only firestore
```

<br>

## Firestore overview

| Collection | Used by | Role |
|---|---|---|
| `routines` | Portal + Admin | Group codes and weekly class schedules |

Group codes are loaded from `routines` documents (`group_short_code` or doc id). If Firestore is offline, the app falls back to sample codes like `CST 3/1` and `ET 3/1`.

> Keep `firestore.rules` strict in production. Admin write access should require authenticated admin users only.

<br>

## Admin console

- URL path: `/admin`  
- Manage Chapainawabganj Polytechnic class routines  
- Email/password provider enabled in Firebase Auth config  
- Do not commit production passwords or service-account keys  

<br>

## Design notes

- **Layout:** mobile-first “phone frame” portal  
- **Tone:** light UI with soft ambient glows  
- **Accent:** indigo / purple routine cards, slate neutrals for secondary modules  
- **Typography:** Outfit for display, Inter for body  

<br>

## Contributing

1. Prefer small, focused changes under `public/` or Firebase config.  
2. Test locally with `firebase serve` before deploy.  
3. Avoid committing secrets (`.env`, private keys, real admin passwords).  
4. Update this README when you add routes or major features.  

<br>

## License

Private project — all rights reserved unless stated otherwise by the owner.

<br>

<p align="center">
  <sub>Built for CNGPI students.</sub><br>
  <strong>Chapainawabganj Polytechnic Institute</strong>
</p>
