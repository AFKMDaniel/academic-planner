# AGENTS.md

## Project Overview

This is a small desktop course project for the topic:

**"Разработка информационной подсистемы по созданию и заполнению календарно-тематического планирования в соответствии с учебным планом."**

The application is intended to help a teacher create and manage calendar-thematic lesson planning based on a curriculum.

The project is intentionally small and focused on demonstrating:

- a graphical desktop interface;
- database usage;
- basic CRUD operations;
- interaction between related entities;
- persistent local data storage.

This is a **course project**, not a production or enterprise application. Keep the implementation simple and understandable.

---

## Technology Stack

- **Python 3.10**
- **PySide6** — desktop graphical interface
- **SQLite** — local database
- **SQLAlchemy** — ORM and database access
- **pytest 8.4.2** — автоматизированное тестирование
- **PyInstaller** — Windows `.exe` packaging

---

## Architecture

Use a simple layered structure with clear separation of responsibilities.

Recommended structure:

```text
app/
├── main.py
├── database/
├── models/
├── services/
└── ui/

tests/
resources/

requirements.txt
README.md
.gitignore
```

### `database/`

Database configuration, engine, sessions, and initialization.

### `models/`

SQLAlchemy models representing application entities and their relationships.

### `services/`

Application and data-access logic that should not be tied directly to UI widgets.

### `ui/`

PySide6 windows, pages, dialogs, widgets, and UI-related code.

### `tests/`

Small set of tests for important application functionality.

### `resources/`

Application resources such as stylesheets and other static files.

Keep dependencies between layers straightforward:

```text
UI → Services → Models / Database
```

Avoid unnecessary architectural patterns, abstractions, or frameworks.

---

## Main Domain Entities

The application is centered around four main entities:

- **Subject** — an academic subject.
- **Curriculum** — an academic curriculum for a particular group and academic year.
- **CurriculumSubject** — a subject included in a curriculum with its planned number of hours.
- **Lesson** — an individual lesson belonging to a curriculum subject.

Relationships between these entities should be represented using SQLAlchemy relationships and foreign keys.

---

## UI Style

The interface should be:

- simple;
- clean;
- consistent;
- easy to understand;
- suitable for a small educational desktop application.

Prefer standard PySide6 widgets and layouts.

Use Qt Style Sheets where they improve consistency, but avoid excessive visual customization.

The UI should prioritize functionality and clarity over visual complexity.

---

## Code Style

Write straightforward, maintainable Python code.

Prefer:

- meaningful names;
- small focused functions;
- clear class responsibilities;
- type hints where useful;
- minimal duplication.

Avoid:

- unnecessary abstractions;
- over-engineering;
- overly complex design patterns;
- large monolithic classes;
- unnecessary dependencies.

Follow the existing project structure and style when extending the application.

---

## Project Scope

Keep the project intentionally limited in size.

Do not turn it into a large enterprise application or introduce technologies that are not necessary for a local desktop course project.

Features and implementation details will be specified separately in development tasks/prompts.

When there are multiple reasonable technical solutions, prefer the simplest one that fits the existing architecture and project goals.
