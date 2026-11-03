from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.assessments.models import Answer, Assessment, AssessmentQuestion, Attempt, Question, QuestionConcept
from apps.curriculum.models import Concept, ConceptPrerequisite, Course, Lesson, LessonSection, LearningResource, Subject, Unit
from apps.learning.models import AppPreferences, LearningEvent, StudyTask
from apps.notifications.models import Notification
from apps.recovery.models import Intervention, InterventionRecipient, RecoveryPlan, RecoveryStep
from apps.schools.models import Classroom, Enrollment, GuardianLink, School, TeacherAssignment


class Command(BaseCommand):
    help = "Create the deterministic fictional Pathloom demo dataset."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Reset demo records before reseeding.")

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            for model in [Answer, Attempt, AssessmentQuestion, Assessment, QuestionConcept, Question, RecoveryStep, RecoveryPlan, InterventionRecipient, Intervention, StudyTask, AppPreferences, LearningEvent, Notification, ConceptPrerequisite, LessonSection, Lesson, LearningResource, Unit, Course, Concept, Enrollment, TeacherAssignment, GuardianLink, Classroom, User, Subject, School]:
                if model is User:
                    model.objects.filter(is_staff=False).delete()
                else:
                    model.objects.all().delete()
        school, _ = School.objects.get_or_create(name="Horizon Valley Secondary School", defaults={"region": "Bagmati Province", "is_demo": True})
        math, _ = Subject.objects.get_or_create(slug="mathematics", defaults={"display_name": "Mathematics", "icon_key": "sigma", "accent": "indigo"})
        science, _ = Subject.objects.get_or_create(slug="science", defaults={"display_name": "Science", "icon_key": "flask", "accent": "teal"})

        concepts = {}
        concept_data = [
            ("MATH-ALG-01", math, "Order of operations", "Use a consistent order to simplify expressions."),
            ("MATH-ALG-02", math, "Collecting like terms", "Combine terms that share the same variable and exponent."),
            ("MATH-ALG-03", math, "Linear equations in one variable", "Keep both sides balanced while isolating the unknown."),
            ("MATH-ALG-04", math, "Distributive property", "Multiply a factor across every term inside parentheses."),
            ("MATH-ALG-05", math, "Common factor extraction", "Find the greatest shared factor before simplifying."),
            ("MATH-ALG-06", math, "Multiplying binomials", "Use an organised first-outer-inner-last approach."),
            ("MATH-ALG-07", math, "Factorisation of simple quadratic expressions", "Rewrite a quadratic as two useful binomial factors."),
            ("MATH-ALG-08", math, "Quadratic equations by factorisation", "Use zero-product reasoning after factoring."),
            ("MATH-ALG-09", math, "Coordinate plane basics", "Read and plot ordered pairs on a coordinate plane."),
            ("MATH-ALG-10", math, "Slope between two points", "Compare vertical change with horizontal change."),
            ("SCI-PHY-01", science, "Force and motion basics", "Describe how pushes and pulls affect motion."),
            ("SCI-PHY-02", science, "Speed and velocity", "Relate distance, direction and elapsed time."),
            ("SCI-PHY-03", science, "Acceleration and graphs", "Interpret changing velocity from a graph."),
            ("SCI-PHY-04", science, "Electrical current", "Explain charge flow through a conducting path."),
            ("SCI-PHY-05", science, "Voltage and resistance", "Relate potential difference, current and resistance."),
            ("SCI-PHY-06", science, "Simple series circuits", "Trace current through components in one loop."),
            ("SCI-CHEM-01", science, "Elements and compounds", "Distinguish pure elements from combined substances."),
            ("SCI-CHEM-02", science, "Chemical reaction types", "Recognise common patterns in chemical changes."),
            ("SCI-CHEM-03", science, "Balancing simple equations", "Conserve each kind of atom on both sides."),
            ("MATH9-GEO-01", math, "Triangles and angle relationships", "Use known angle relationships to reason about shapes."),
            ("MATH9-GEO-02", math, "Area and scale", "Connect dimensions, area and scale drawings."),
            ("SCI9-LIFE-01", science, "Cell structures", "Match basic cell parts to their functions."),
            ("SCI9-LIFE-02", science, "Ecosystems and energy", "Trace energy through a simple food web."),
            ("SCI9-LIFE-03", science, "Health and environment", "Connect everyday choices to environmental health."),
            ("MATH-ALG-11", math, "Quadratic graphs", "Connect roots and shape to a quadratic graph."),
        ]
        for key, subject, title, description in concept_data:
            concepts[key], _ = Concept.objects.update_or_create(id=key, defaults={"subject": subject, "title": title, "description": description})
        prerequisites = [("MATH-ALG-02", "MATH-ALG-03"), ("MATH-ALG-04", "MATH-ALG-05"), ("MATH-ALG-05", "MATH-ALG-07"), ("MATH-ALG-06", "MATH-ALG-07"), ("MATH-ALG-07", "MATH-ALG-08"), ("MATH-ALG-09", "MATH-ALG-10"), ("SCI-PHY-01", "SCI-PHY-02"), ("SCI-PHY-02", "SCI-PHY-03"), ("SCI-PHY-04", "SCI-PHY-05"), ("SCI-PHY-05", "SCI-PHY-06"), ("SCI-CHEM-01", "SCI-CHEM-02"), ("SCI-CHEM-02", "SCI-CHEM-03"), ("MATH-ALG-08", "MATH-ALG-11")]
        for prerequisite, concept in prerequisites:
            ConceptPrerequisite.objects.get_or_create(prerequisite=concepts[prerequisite], concept=concepts[concept])

        math_course, _ = Course.objects.get_or_create(id="c0000000-0000-0000-0000-000000000010", defaults={"subject": math, "grade": 10, "title": "Grade 10 Mathematics", "description": "A focused pathway through algebra, quadratics and coordinate geometry.", "estimated_minutes": 480})
        science_course, _ = Course.objects.get_or_create(id="c0000000-0000-0000-0000-000000000011", defaults={"subject": science, "grade": 10, "title": "Grade 10 Science", "description": "Evidence-led practice across motion, circuits and chemical change.", "estimated_minutes": 420})
        grade9_course, _ = Course.objects.get_or_create(id="c0000000-0000-0000-0000-000000000012", defaults={"subject": math, "grade": 9, "title": "Grade 9 Mathematics Foundations", "description": "Illustrative Grade 9 foundations that lead into the Grade 10 pathway.", "estimated_minutes": 300})

        lesson_specs = [
            (math_course, "01", "Algebra foundations", [("Simplify with confidence", ["MATH-ALG-01", "MATH-ALG-02"]), ("Balance a linear equation", ["MATH-ALG-03"])]),
            (math_course, "02", "Factorisation toolkit", [("The shared factor", ["MATH-ALG-04", "MATH-ALG-05"]), ("Factoring x² + 5x + 6", ["MATH-ALG-06", "MATH-ALG-07"])]),
            (math_course, "03", "Quadratic equations", [("From factors to roots", ["MATH-ALG-08"]), ("Quadratic graph connections", ["MATH-ALG-11"])]),
            (math_course, "04", "Coordinate geometry", [("Read the coordinate plane", ["MATH-ALG-09"]), ("Slope as a rate", ["MATH-ALG-10"])]),
            (science_course, "01", "Forces and motion", [("A force changes motion", ["SCI-PHY-01"]), ("Speed and velocity", ["SCI-PHY-02", "SCI-PHY-03"])]),
            (science_course, "02", "Electricity in context", [("Current in a circuit", ["SCI-PHY-04"]), ("Voltage and resistance", ["SCI-PHY-05", "SCI-PHY-06"])]),
            (science_course, "03", "Chemical change", [("Elements and compounds", ["SCI-CHEM-01"]), ("Balancing reactions", ["SCI-CHEM-02", "SCI-CHEM-03"])]),
            (grade9_course, "01", "Geometry foundations", [("Angles in triangles", ["MATH9-GEO-01"]), ("Area and scale", ["MATH9-GEO-02"])]),
            (grade9_course, "02", "Living systems", [("Inside a cell", ["SCI9-LIFE-01"]), ("Energy in ecosystems", ["SCI9-LIFE-02", "SCI9-LIFE-03"])]),
        ]
        lessons = []
        for course, unit_code, unit_title, specs in lesson_specs:
            unit, _ = Unit.objects.get_or_create(course=course, order=int(unit_code), defaults={"title": unit_title})
            unit.title = unit_title
            unit.save(update_fields=["title"])
            for index, (lesson_title, concept_keys) in enumerate(specs, 1):
                lesson, _ = Lesson.objects.get_or_create(unit=unit, title=lesson_title, defaults={"duration_minutes": 14 + index * 4, "summary": f"An original Pathloom micro-lesson for {lesson_title.lower()}."})
                lesson.concepts.set([concepts[key] for key in concept_keys])
                for section_order, section_title in enumerate(["Notice the pattern", "Try the worked step", "Say it back"], 1):
                    section, _ = LessonSection.objects.get_or_create(lesson=lesson, order=section_order, defaults={"title": section_title, "content": self.section_copy(lesson_title, section_title), "timestamp_start": (section_order - 1) * 90, "timestamp_end": section_order * 90})
                    section.concepts.set([concepts[key] for key in concept_keys])
                resource, _ = LearningResource.objects.get_or_create(title=f"Worked example: {lesson_title}", defaults={"resource_type": LearningResource.Types.WORKED_EXAMPLE, "length_minutes": 10, "lesson": lesson, "body": self.resource_copy(lesson_title)})
                resource.lesson = lesson
                resource.save(update_fields=["lesson"])
                resource.concepts.set([concepts[key] for key in concept_keys])
                lessons.append(lesson)

        questions = {}
        question_specs = [
            ("q-math-01", "Simplify 3x + 2x.", ["5x", "3x", "6x", "x"], "5x", "Combine the coefficients of like terms: 3 + 2 = 5.", ["MATH-ALG-02"]),
            ("q-math-02", "Factorise x² + 5x + 6.", ["(x+2)(x+3)", "(x+1)(x+6)", "(x+5)(x+1)", "(x+2)(x-3)"], "(x+2)(x+3)", "Find two numbers that multiply to 6 and add to 5: 2 and 3.", ["MATH-ALG-07"]),
            ("q-math-03", "Which pair solves x² + 5x + 6 = 0?", ["x = -2 or -3", "x = 2 or 3", "x = -1 or -6", "x = 0 or 6"], "x = -2 or -3", "The zero-product rule gives x + 2 = 0 or x + 3 = 0.", ["MATH-ALG-08", "MATH-ALG-07"]),
            ("q-math-04", "What is the common factor of 6x + 9?", ["3", "6", "9", "x"], "3", "Both terms are divisible by 3.", ["MATH-ALG-05"]),
            ("q-math-05", "The roots of x² + 7x + 12 = 0 are", ["-3 and -4", "3 and 4", "-2 and -6", "2 and 6"], "-3 and -4", "(x + 3)(x + 4) = 0.", ["MATH-ALG-08"]),
            ("q-math-07", "Factorise x² + 7x + 12.", ["(x+3)(x+4)", "(x+2)(x+6)", "(x+1)(x+12)", "(x-3)(x-4)"], "(x+3)(x+4)", "Find two numbers that multiply to 12 and add to 7: 3 and 4.", ["MATH-ALG-07"]),
            ("q-sci-01", "A car travels 120 m in 10 s. What is its speed?", ["12 m/s", "1200 m/s", "0.08 m/s", "110 m/s"], "12 m/s", "Speed is distance divided by time: 120 ÷ 10 = 12 m/s.", ["SCI-PHY-02"]),
            ("q-sci-02", "If voltage is 12 V and resistance is 4 Ω, current is", ["3 A", "48 A", "0.3 A", "8 A"], "3 A", "Using I = V/R, 12 V ÷ 4 Ω = 3 A.", ["SCI-PHY-05"]),
            ("q-sci-03", "Which is a compound?", ["Water", "Oxygen", "Copper", "Helium"], "Water", "Water contains hydrogen and oxygen chemically joined.", ["SCI-CHEM-01"]),
            ("q-sci-04", "A balanced equation conserves", ["Each kind of atom", "The temperature only", "The colour", "The container size"], "Each kind of atom", "Atoms are rearranged, not created or destroyed.", ["SCI-CHEM-03"]),
        ]
        for key, prompt, options, correct, explanation, concept_keys in question_specs:
            question, _ = Question.objects.update_or_create(id=key, defaults={"prompt": prompt, "question_type": Question.Types.MULTIPLE_CHOICE, "options": options, "correct_answer": correct, "explanation": explanation, "difficulty": "developing"})
            question.concepts.set([concepts[item] for item in concept_keys])
            questions[key] = question
        numeric, _ = Question.objects.update_or_create(id="q-math-06", defaults={"prompt": "What is the value of x if 2x + 4 = 10? Enter a number.", "question_type": Question.Types.NUMERIC, "options": [], "correct_answer": "3", "explanation": "Subtract 4, then divide by 2: x = 3.", "difficulty": "developing"})
        numeric.concepts.set([concepts["MATH-ALG-03"]])
        questions[numeric.id] = numeric
        assessment, _ = Assessment.objects.update_or_create(id="assessment-math-diagnostic", defaults={"course": math_course, "title": "Algebra signal check", "description": "A short evaluation of the ideas behind factorisation and quadratic equations.", "max_attempts": 10})
        assessment.questions.clear()
        for order, key in enumerate(["q-math-01", "q-math-02", "q-math-03", "q-math-04", "q-math-06"], 1):
            AssessmentQuestion.objects.create(assessment=assessment, question=questions[key], order=order)
        fresh_math, _ = Assessment.objects.update_or_create(id="assessment-math-fresh", defaults={"course": math_course, "title": "Factorisation transfer check", "description": "A fresh set of related questions to check whether the factor-pair idea transfers to a new expression.", "max_attempts": 10})
        fresh_math.questions.clear()
        for order, key in enumerate(["q-math-07", "q-math-05", "q-math-04", "q-math-06"], 1):
            AssessmentQuestion.objects.create(assessment=fresh_math, question=questions[key], order=order)
        science_assessment, _ = Assessment.objects.update_or_create(id="assessment-science-check", defaults={"course": science_course, "title": "Science evidence check", "description": "A compact practice set covering motion, circuits and matter.", "max_attempts": 10})
        science_assessment.questions.clear()
        for order, key in enumerate(["q-sci-01", "q-sci-02", "q-sci-03", "q-sci-04"], 1):
            AssessmentQuestion.objects.create(assessment=science_assessment, question=questions[key], order=order)

        admin = User.objects.filter(username="demo_admin").first()
        if not admin:
            admin = User.objects.create_superuser("demo_admin", "demo@example.test", "demo-admin-password")
        admin.display_name = "Pathloom Demo Admin"
        admin.role = User.Roles.COORDINATOR
        admin.avatar_initials = "PA"
        admin.school = school
        admin.save()
        personas = [
            ("sahana", "Sahana Shrestha", User.Roles.STUDENT, "SS"), ("nischal", "Nischal Rai", User.Roles.STUDENT, "NR"), ("aditi", "Aditi Gurung", User.Roles.STUDENT, "AG"), ("ramesh", "Ramesh Karki", User.Roles.STUDENT, "RK"), ("priya", "Priya Tamang", User.Roles.STUDENT, "PT"), ("kabir", "Kabir Joshi", User.Roles.STUDENT, "KJ"), ("maya", "Maya Lama", User.Roles.STUDENT, "ML"), ("anish", "Anish Shrestha", User.Roles.STUDENT, "AS"), ("sujal", "Sujal Rai", User.Roles.STUDENT, "SR"), ("nima", "Nima Sherpa", User.Roles.STUDENT, "NS"), ("rina", "Ms. Rina Karki", User.Roles.TEACHER, "RK"), ("bibek", "Mr. Bibek Shahi", User.Roles.TEACHER, "BS"), ("suman", "Mr. Suman Thapa", User.Roles.COORDINATOR, "ST"), ("guardian_sahana", "Sahana's Guardian", User.Roles.GUARDIAN, "SG")]
        users = {}
        for username, display_name, role, initials in personas:
            user, _ = User.objects.get_or_create(username=username, defaults={"display_name": display_name, "role": role, "avatar_initials": initials, "school": school})
            user.display_name, user.role, user.avatar_initials, user.school = display_name, role, initials, school
            if username == "suman":
                user.is_staff = True
            user.set_unusable_password()
            user.save()
            users[username] = user
        math_class, _ = Classroom.objects.get_or_create(school=school, name="Grade 10 · Mathematics A", subject=math, defaults={"grade": 10, "section": "A"})
        science_class, _ = Classroom.objects.get_or_create(school=school, name="Grade 10 · Science A", subject=science, defaults={"grade": 10, "section": "A"})
        grade9_class, _ = Classroom.objects.get_or_create(school=school, name="Grade 9 · Foundations", subject=math, defaults={"grade": 9, "section": "B"})
        TeacherAssignment.objects.get_or_create(classroom=math_class, teacher=users["rina"])
        TeacherAssignment.objects.get_or_create(classroom=science_class, teacher=users["bibek"])
        for username in ["sahana", "nischal", "ramesh", "priya", "kabir", "maya"]:
            Enrollment.objects.get_or_create(classroom=math_class, student=users[username])
        for username in ["sahana", "nischal", "aditi", "anish", "sujal", "nima"]:
            Enrollment.objects.get_or_create(classroom=science_class, student=users[username])
        for username in ["aditi", "anish", "sujal", "nima"]:
            Enrollment.objects.get_or_create(classroom=grade9_class, student=users[username])
        GuardianLink.objects.get_or_create(guardian=users["guardian_sahana"], learner=users["sahana"], relationship="Parent / guardian")

        self.seed_attempt(users["sahana"], assessment, ["5x", "(x+1)(x+6)", "x = -2 or -3", "3", "3"], days_ago=3)
        self.seed_attempt(users["sahana"], science_assessment, ["12 m/s", "3 A", "Water", "Each kind of atom"], days_ago=8)
        self.seed_attempt(users["nischal"], assessment, ["5x", "(x+2)(x+3)", "x = -2 or -3", "3", "3"], days_ago=5)
        self.seed_attempt(users["nischal"], science_assessment, ["12 m/s", "48 A", "Water", "Each kind of atom"], days_ago=10)
        self.seed_attempt(users["aditi"], science_assessment, ["12 m/s", "3 A", "Water", "Each kind of atom"], days_ago=12)
        self.seed_attempt(users["ramesh"], assessment, ["5x", "(x+2)(x+3)", "x = 2 or 3", "3", "3"], days_ago=15)
        for username in ["sahana", "nischal", "ramesh", "priya", "kabir", "maya"]:
            learner = users[username]
            StudyTask.objects.get_or_create(learner=learner, title="Recall: factor pairs", defaults={"concept": concepts["MATH-ALG-07"], "due_date": timezone.localdate() + timedelta(days=1), "minutes": 15, "source": "RECOMMENDED"})
            StudyTask.objects.get_or_create(learner=learner, title="Two-question science check", defaults={"concept": concepts["SCI-PHY-05"], "due_date": timezone.localdate() + timedelta(days=3), "minutes": 12, "source": "SPACED_RECALL"})
        plans = []
        plan = RecoveryPlan.objects.filter(learner=users["sahana"], originating_concept=concepts["MATH-ALG-07"]).first()
        if not plan:
            plan = RecoveryPlan.objects.create(learner=users["sahana"], originating_concept=concepts["MATH-ALG-07"], reason="Two recent responses suggest the factor-pair step is the most useful place to slow down. This is a suggested prerequisite, not a diagnosis.", evidence_ids=["answer-seeded-factor-1", "answer-seeded-factor-2"])
            resource = LearningResource.objects.filter(concepts=concepts["MATH-ALG-07"]).first()
            RecoveryStep.objects.create(plan=plan, step_type=RecoveryStep.Types.LESSON, resource=resource, sequence=1, instruction="Review the worked example x² + 5x + 6 and annotate the two numbers that make the pair.")
            RecoveryStep.objects.create(plan=plan, step_type=RecoveryStep.Types.REFLECTION, resource=resource, sequence=2, instruction="Explain why the signs of the two factors must be positive.")
            RecoveryStep.objects.create(plan=plan, step_type=RecoveryStep.Types.PRACTICE, resource=resource, sequence=3, instruction="Try a fresh equivalent factorisation before opening the answer explanation.")
        plan2, _ = RecoveryPlan.objects.get_or_create(learner=users["nischal"], originating_concept=concepts["SCI-PHY-05"], defaults={"reason": "Voltage and resistance practice is ready for a short revisit.", "status": RecoveryPlan.Status.COMPLETED})
        plan3, _ = RecoveryPlan.objects.get_or_create(learner=users["aditi"], originating_concept=concepts["MATH9-GEO-01"], defaults={"reason": "There is not enough evidence yet for a precise estimate; a small diagnostic would help.", "status": RecoveryPlan.Status.INCONCLUSIVE})
        intervention, _ = Intervention.objects.get_or_create(teacher=users["rina"], concept=concepts["MATH-ALG-07"], defaults={"note": "Use the shared factor-pair example, then ask learners to explain the choice of numbers.", "due_date": timezone.localdate() + timedelta(days=4), "status": Intervention.Status.ASSIGNED})
        for username in ["sahana", "nischal"]:
            InterventionRecipient.objects.get_or_create(intervention=intervention, learner=users[username])
        for recipient in [users["sahana"], users["nischal"]]:
            Notification.objects.get_or_create(recipient=recipient, title="A focused practice path is ready", defaults={"body": "Your factorisation recovery steps are waiting in Recovery Center.", "destination": "/student/recovery"})
        Notification.objects.get_or_create(recipient=users["rina"], title="Factorisation is a class opportunity", defaults={"body": "Review the shared evidence and consider a targeted intervention.", "destination": "/teacher/concept-insights"})
        self.stdout.write(self.style.SUCCESS("Seeded Pathloom demo data for fictional Horizon Valley Secondary School."))

    def seed_attempt(self, learner, assessment, responses, days_ago):
        attempt, created = Attempt.objects.get_or_create(learner=learner, assessment=assessment, attempt_key=f"seed-{learner.username}-{assessment.id}", defaults={"total": assessment.questions.count()})
        if not created:
            return attempt
        score = 0
        for question, response in zip(assessment.questions.all(), responses):
            correct = response.strip().casefold() == question.correct_answer.strip().casefold()
            score += int(correct)
            Answer.objects.create(attempt=attempt, question=question, response=response, is_correct=correct, confidence="confident" if correct else "unsure")
        timestamp = timezone.now() - timedelta(days=days_ago)
        Attempt.objects.filter(id=attempt.id).update(score=score, total=assessment.questions.count(), submitted_at=timestamp, started_at=timestamp - timedelta(minutes=18))
        event, _ = LearningEvent.objects.get_or_create(learner=learner, event_type=LearningEvent.Types.ASSESSMENT_SUBMITTED, metadata={"attempt_id": str(attempt.id), "score": score, "total": assessment.questions.count()})
        event.concepts.set(Concept.objects.filter(questions__assessments=assessment).distinct())
        return Attempt.objects.get(id=attempt.id)

    def section_copy(self, lesson_title, section_title):
        if "Factoring" in lesson_title:
            return {"Notice the pattern": "For x² + 5x + 6, look for two numbers that multiply to 6 and add to 5.", "Try the worked step": "The pair 2 and 3 gives (x + 2)(x + 3). Expanding checks the idea: x² + 3x + 2x + 6.", "Say it back": "A useful factor pair must satisfy both the product and the sum."}[section_title]
        if "Voltage" in lesson_title:
            return {"Notice the pattern": "Voltage is the push; resistance is the opposition to current.", "Try the worked step": "With 12 V across 4 Ω, I = V/R = 3 A.", "Say it back": "Increasing resistance reduces current when voltage stays fixed."}[section_title]
        return f"{section_title}: {lesson_title} is explained with an original Pathloom example and one check for understanding."

    def resource_copy(self, lesson_title):
        return f"This original demo resource supports {lesson_title}. Pause after each transformation, then explain the reason in your own words."
