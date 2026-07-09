Inference Runner                     Alert Backend                        Flutter App
─────────────────                    ─────────────                        ───────────
fall_detector_logic/                 alert_python_backend/                fall_alert/
runners/                             alert_sender.py                      lib/pages/
_handle_alerts()                        │                                  home_page.dart
  │                                    │                                  │
  ├─ fall detected (3 consecutive)     │                                  │
  │   → POST /predictions              │                                  │
  │     {"status": "fall"}  ──────────►│ stores state = "fall"            │
  │                                    │ sends FCM push notification ────►│ background notification
  │                                    │                                  │
  │                                    │ GET /status ◄────────────────────│ polls every 1s
  │                                    │   → {"status": "fall"} ─────────►│ triggerFall() → red UI
  │                                    │                                  │
  │                                    │ POST /acknowledge ◄──────────────│ user taps "Okay"
  │                                    │   → state = "normal"             │
  │                                    │   → fall_locked = false          │
  ├─ no fall                           │                                  │
  │   → POST /predictions             │                                  │
  │     {"status": "normal"} ────────►│ stores state = "normal"          │
  │                                    │ GET /status ◄────────────────────│ polls every 1s
  │                                    │   → {"status": "normal"} ───────►│ resetToNormal() → green UI


## FLOWCHART

```mermaid
graph TD
    %% Nodes for Inference Runner
    subgraph IR [Inference Runner<br/>fall_detector_logic/runners/]
        A[Handle Alerts]
        B{3 Consecutive Falls?}
        C[POST /predictions <br/> status: fall]
        D[POST /predictions <br/> status: normal]
    end

    %% Nodes for Alert Backend
    subgraph AB [Alert Backend<br/>alert_python_backend/]
        E[Store state = 'fall']
        F[Send FCM Push Notification]
        G[Store state = 'normal']
        H{GET /status}
        I[POST /acknowledge]
    end

    %% Nodes for Flutter App
    subgraph FA [Flutter App<br/>fall_alert/lib/]
        J[Background Notification]
        K[Poll /status every 1s]
        L{Status Check}
        M[triggerFall -> Red UI]
        N[resetToNormal -> Green UI]
        O[User taps 'Okay']
    end

    %% Logic Flow
    A --> B
    B -- Yes --> C
    B -- No --> D

    %% Fall Detection Path
    C --> E
    E --> F
    F -.-> J
    
    %% Polling & UI Logic
    K --> H
    H --> L
    L -- status: fall --> M
    L -- status: normal --> N

    %% Acknowledgment Path
    M --> O
    O --> I
    I --> G
    D --> G

    %% Styling
    style M fill:#ff9999,stroke:#333
    style N fill:#99ff99,stroke:#333
    style C fill:#f9f,stroke:#333
    style I fill:#bbf,stroke:#333
```