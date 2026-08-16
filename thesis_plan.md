# Official Thesis Structure & Master Plan (Sabaragamuwa University PST Department)

This master plan reflects the exact official thesis structure sent by your department (`Thesis Structure (1).pdf`) and the formatting guidelines from the PST Handbook.

---

## 1. Official Departmental Chapter & Section Structure

Every chapter **must** end with a **"Summary for the Chapter"** section as mandated by the department guidelines.

```
PRELIMINARY PAGES (Roman Numerals: i, ii, iii, iv, v, vi, vii, viii, ix)
├── Title Page (Page i)
├── DECLARATION (Page ii)
├── CERTIFICATION OF APPROVAL (Page iii)
├── ACKNOWLEDGEMENT (Page iv)
├── ABSTRACT & Keywords (Page v)
├── CONTENTS (Page vi)
├── LIST OF FIGURES (Page viii)
└── LIST OF TABLES (Page ix)

BODY OF DISSERTATION (Arabic Numerals: 1, 2, 3...)

CHAPTER 01: INTRODUCTION (~7–8 pages)
├── 1.1 Preamble
├── 1.2 Background
├── 1.3 Problem Statement / Hypothesis
├── 1.4 Proposed Model (Overview of Logarithmic, Harmonic & Hybrid Framework)
├── 1.5 Objectives
│   ├── 1.5.1 Main Objective
│   └── 1.5.2 Sub Objectives
├── 1.6 Structure of the Thesis
└── 1.7 Summary for the Chapter

CHAPTER 02: LITERATURE REVIEW (~12–15 pages)
├── 2.1 Introduction
├── 2.2 Existing Works (Dynamic array growth, C++ 2.0x, Java 1.5x, CPython 1.125x, Brodnik, Sartor, Bille)
├── 2.3 Research Gap (Lack of workload-aware, velocity-sensitive dynamic growth algorithms)
└── 2.4 Summary for the Chapter

CHAPTER 03: METHODOLOGY (~14–16 pages)
├── 3.1 Introduction
├── 3.2 Materials (Python 3.11 simulator, skopt, matplotlib, numpy, hardware environment)
├── 3.3 Research Design (Experimental design, Formula A, B, C, D formulations & clamping)
├── 3.4 Data Collection (7 Workload insertion patterns & Velocity metric v = delta_N / delta_t)
├── 3.5 Data Analysis (Composite J-Score objective function: 0.4 Waste + 0.4 Copies + 0.2 Time)
├── 3.6 Implementation (Simulator architecture & dynamic growth engine implementation)
├── 3.7 Evaluation (Grid Search benchmarking & Gaussian Process Bayesian Optimization setup)
└── 3.8 Summary for the Chapter

CHAPTER 04: RESULTS AND EVALUATION (~16–18 pages)
├── 4.1 Introduction
├── 4.2 Benchmark Results & Performance Comparison (Standardized at 10M insertions across 7 patterns)
├── 4.3 Detailed Formula Evaluation (Formula A, B, C, D comparisons vs Fixed 2.0x, 1.5x, Python List)
├── 4.4 Parameter Sensitivity Analysis (Alpha, Beta, C0, Lambda, Weight wA sensitivity curves)
└── 4.5 Summary for the Chapter

CHAPTER 05: CONCLUSION (~4–5 pages)
├── 5.1 Introduction
├── 5.2 Summary of Findings
├── 5.3 Conclusion Drawn by Results
├── 5.4 Limitations (Timestamp measurement overhead, simulation boundaries)
└── 5.5 Future Works (C++ STL std::vector integration, embedded IoT microcontrollers)

BACK MATTER
├── REFERENCES (IEEE Style format)
└── APPENDICES
    ├── Appendix 1: Publication Evidence / Paper Abstracts
    └── Appendix 2: Python Simulator Source Code & CSV Benchmark Logs
```

---

## 2. Formatting & Style Specifications

| Parameter                            | Official PST Requirement                   | LaTeX Command                                   |
| :----------------------------------- | :----------------------------------------- | :---------------------------------------------- |
| **Paper Size**                 | A4                                         | `\documentclass[12pt, a4paper]{report}`       |
| **Font Family**                | Times New Roman                            | `\usepackage{times}`                          |
| **Font Size**                  | 12pt                                       | `12pt`                                        |
| **Line Spacing**               | 1.5 lines                                  | `\usepackage{setspace}` + `\onehalfspacing` |
| **Left Margin (Binding)**      | **4.0 cm (1.5 inch)**                | `left=4.0cm` (geometry package)               |
| **Right, Top, Bottom Margins** | **2.5 cm (1.0 inch)**                | `right=2.5cm, top=2.5cm, bottom=2.5cm`        |
| **Alignment**                  | Justified                                  | Default LaTeX justified                         |
| **Page Numbering**             | Bottom Right-hand corner                   | `\rfoot{\thepage}` (fancyhdr package)         |
| **Preliminary Numbering**      | Lowercase Roman (`i, ii, iii...`)        | `\pagenumbering{roman}`                       |
| **Body Page Numbering**        | Arabic (`1, 2, 3...`) starting Chapter 1 | `\pagenumbering{arabic}`                      |

---

## 3. Title Page & Preliminary Exact Text

### Degree Statement on Title Page (Page `i`):

```latex
A dissertation submitted in partial fulfilment of the requirements for the
Bachelor of Science Honours Degree Examination
In
Computer Science and Technology

Department of Physical Sciences and Technology,
Faculty of Applied Sciences,
Sabaragamuwa University of Sri Lanka
Sri Lanka.
2025/2026
```

### Declaration Text (Page `ii`):

```latex
DECLARATION
I declare that this Report does not incorporate, without acknowledgment, any material 
previously submitted for a degree or a Diploma in any University and to the best of my 
knowledge and belief, it does not contain any material previously published or written by 
another person or myself except where due reference is made in the text.
Also, I hereby grant to Sabaragamuwa University of Sri Lanka the non-exclusive right to 
reproduce and distribute my Report, in whole or in part in print, electronic or other medium. I 
retain the right to use this content in whole or part in future works (such as articles or books).
```

### Certification of Approval Text (Page `iii`):

```latex
CERTIFICATION OF APPROVAL
We hereby declare that this Report is from the student’s own work and effort, and all other 
sources of information used have been acknowledged. This Report has been submitted 
with our approval.
```

---

## 4. 60-Page Target Allocation Budget

| Section / Chapter                                                              |  Target Page Range  |
| :----------------------------------------------------------------------------- | :-----------------: |
| Preliminary Pages (Title, Declaration, Approval, Ack, Abstract, TOC, LOF, LOT) |      ~9 pages      |
| Chapter 01: Introduction                                                       |     ~7–8 pages     |
| Chapter 02: Literature Review                                                  |    ~12–15 pages    |
| Chapter 03: Methodology                                                        |    ~14–16 pages    |
| Chapter 04: Results and Evaluation                                             |    ~16–18 pages    |
| Chapter 05: Conclusion                                                         |     ~4–5 pages     |
| References (IEEE format)                                                       |     ~3–4 pages     |
| Appendices (Source code & CSV tables)                                          |     ~5–8 pages     |
| **TOTAL ESTIMATED THESIS PAGE COUNT**                                    | **~60 Pages** |
