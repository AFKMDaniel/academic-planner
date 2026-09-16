LESSON_TYPE_LABELS = {
    "Lecture": "Лекция",
    "Practical": "Практическое занятие",
    "Laboratory": "Лабораторное занятие",
    "Test": "Зачёт",
}


def lesson_type_label(lesson_type: str) -> str:
    return LESSON_TYPE_LABELS.get(lesson_type, lesson_type)
