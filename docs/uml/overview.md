# Sơ đồ luồng và mô hình dữ liệu

## Use case / luồng người dùng

~~~mermaid
flowchart LR
    U[Người dùng] -->|Chọn CSV/XLSX| DM[Data Management]
    DM --> V[Kiểm tra cột và dữ liệu]
    V -->|Nhấn Chạy phân tích| P[Pipeline phân tích]
    P --> A[Grade Anomaly Detection]
    P --> G[Grade Adjustment]
    P --> T[Student Profiling / TCI]
    A --> O[Overview Dashboard]
    G --> O
    T --> O
    U --> O
~~~

## Component view

~~~mermaid
flowchart TB
    APP[Streamlit app.py] --> LOAD[src/data_loader.py]
    APP --> PIPE[src/pipeline.py]
    PIPE --> ANOM[src/anomaly_detection.py]
    PIPE --> ADJ[src/grade_adjustment.py]
    PIPE --> TCI[src/tci_calculator.py]
    LOAD --> MEM[(DataFrame trong phiên)]
    ANOM --> MEM
    ADJ --> MEM
    TCI --> MEM
~~~

## Mô hình dữ liệu logic

~~~mermaid
erDiagram
    STUDENT ||--o{ ENROLLMENT : has
    COURSE ||--o{ SECTION : offered_as
    SECTION ||--o{ ENROLLMENT : contains
    STUDENT {
        string student_id
        string cohort
        string faculty
    }
    COURSE {
        string course_id
        string course_group
        int credits
        boolean project_flag
    }
    SECTION {
        string section_id
        string school_year
        int semester
    }
    ENROLLMENT {
        float raw_grade
        float adjusted_score
        float anomaly_score
        float tci_contribution
    }
~~~

Thời khóa biểu được giữ ngoài mô hình liên kết vì mã lớp/môn không tương thích với
bảng điểm.
