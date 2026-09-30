import streamlit as st


# ============================================================
# DAILY STUDY SCHEDULE
# ============================================================

def create_daily_schedule(study_plan, days=7):
    """
    Convert the priority study plan into a simple
    day-by-day study schedule.
    """

    if not study_plan:
        return []

    schedule = []

    total_topics = len(study_plan)

    # Create schedule for each day
    for day in range(1, days + 1):

        # Repeat topics if number of days is greater
        # than number of study-plan topics
        index = (day - 1) % total_topics

        item = study_plan[index]

        topic = item.get(
            "topic",
            "Study Topic"
        )

        reason = item.get(
            "reason",
            "Needs attention"
        )

        suggested_time = item.get(
            "suggested_time",
            item.get("time", "1 day")
        )

        # Get priority
        priority = item.get(
            "priority",
            3
        )

        try:
            priority = int(priority)
        except (ValueError, TypeError):
            priority = 3

        # Decide study activity based on priority
        if priority == 1:

            activity = "Deep Study"

            task_1 = "Concept learning"
            task_1_time = 45

            task_2 = "Practice questions"
            task_2_time = 30

            task_3 = "Quick revision"
            task_3_time = 15

        elif priority == 2:

            activity = "Focused Study"

            task_1 = "Concept learning"
            task_1_time = 40

            task_2 = "Practice"
            task_2_time = 35

            task_3 = "Quick revision"
            task_3_time = 15

        else:

            activity = "Revision & Practice"

            task_1 = "Revision"
            task_1_time = 35

            task_2 = "Practice questions"
            task_2_time = 40

            task_3 = "Self-test"
            task_3_time = 15

        # Add the day to schedule
        schedule.append(
            {
                "day": day,
                "topic": topic,
                "activity": activity,
                "reason": reason,
                "time": suggested_time,

                # 90-minute daily schedule
                "total_minutes": 90,

                "task_1": task_1,
                "task_1_time": task_1_time,

                "task_2": task_2,
                "task_2_time": task_2_time,

                "task_3": task_3,
                "task_3_time": task_3_time,

                "priority": priority,
            }
        )

    return schedule


# ============================================================
# STUDY PROGRESS TRACKER
# ============================================================

def show_progress_tracker(schedule):
    """
    Display the student's study progress.

    Students can mark each study day as completed.
    """

    st.subheader("📊 Study Progress")

    # No schedule available
    if not schedule:

        st.info(
            "Generate a study plan first to start tracking progress."
        )

        return

    # Total number of days
    total_days = len(schedule)

    # Make sure session state exists
    if "completed_tasks" not in st.session_state:

        st.session_state.completed_tasks = set()

    # Count completed days
    completed_days = 0

    for day in schedule:

        day_number = day["day"]

        task_key = f"day_{day_number}"

        if task_key in st.session_state.completed_tasks:

            completed_days += 1

    # Calculate progress
    progress = completed_days / total_days

    percentage = int(progress * 100)

    # ========================================================
    # PROGRESS SUMMARY
    # ========================================================

    st.progress(progress)

    st.write(
        f"### 🎯 {completed_days}/{total_days} days completed — {percentage}%"
    )

    # Three statistics
    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Completed",
            completed_days
        )

    with col2:

        st.metric(
            "Remaining",
            total_days - completed_days
        )

    with col3:

        st.metric(
            "Progress",
            f"{percentage}%"
        )

    st.divider()

    # ========================================================
    # DAILY CHECKLIST
    # ========================================================

    st.subheader("📅 Daily Progress")

    for day in schedule:

        day_number = day["day"]

        topic = day["topic"]

        task_key = f"day_{day_number}"

        # Current checkbox state
        completed = (
            task_key
            in st.session_state.completed_tasks
        )

        # Checkbox
        new_value = st.checkbox(
            f"Day {day_number} — {topic}",
            value=completed,
            key=f"progress_checkbox_{day_number}"
        )

        # Save completion status
        if new_value:

            st.session_state.completed_tasks.add(
                task_key
            )

        else:

            st.session_state.completed_tasks.discard(
                task_key
            )

    st.divider()

    # ========================================================
    # MOTIVATIONAL MESSAGE
    # ========================================================

    if percentage == 100:

        st.success(
            "🎉 Amazing! You completed your entire study plan!"
        )

    elif percentage >= 70:

        st.success(
            "🔥 Great progress! Keep going."
        )

    elif percentage >= 40:

        st.info(
            "💪 Good progress. Stay consistent."
        )

    else:

        st.warning(
            "📚 Start completing your study days."
        )