"""
Sample Data Creator
===================
Generates sample PDF resumes and job flyers for testing the pipeline.
Uses fpdf2 to create realistic-looking PDF documents.

Usage:
    python create_sample_data.py
"""

import os
from fpdf import FPDF, XPos, YPos


def create_sample_resumes(output_dir: str = "data/sample_resumes") -> list[str]:
    """Create sample PDF resumes for testing.

    Args:
        output_dir: Directory to save the sample resumes.

    Returns:
        list[str]: Paths to the created resume files.
    """
    os.makedirs(output_dir, exist_ok=True)
    created_files: list[str] = []

    resumes: list[dict] = [
        {
            "filename": "john_doe_fullstack.pdf",
            "name": "John Doe",
            "email": "john.doe@email.com",
            "phone": "+94 77 123 4567",
            "summary": "Experienced Full-Stack Developer with 5 years of experience building scalable web applications. Proficient in Python, React.js, and cloud technologies.",
            "skills": "Python, React.js, Node.js, PostgreSQL, Docker, Git, REST APIs, TypeScript, MongoDB, Linux",
            "experience": [
                {
                    "role": "Senior Software Engineer",
                    "company": "TechCorp Lanka",
                    "duration": "2022 - Present",
                    "highlights": [
                        "Led development of microservices architecture serving 100K+ users",
                        "Implemented CI/CD pipeline reducing deployment time by 60%",
                        "Mentored 3 junior developers and conducted code reviews",
                    ],
                },
                {
                    "role": "Software Engineer",
                    "company": "Digital Solutions Pvt Ltd",
                    "duration": "2020 - 2022",
                    "highlights": [
                        "Built React.js dashboard for real-time data analytics",
                        "Developed Python REST APIs using FastAPI framework",
                        "Managed PostgreSQL databases with complex query optimization",
                    ],
                },
            ],
            "education": [
                {"degree": "BSc in Computer Science", "institution": "University of Colombo", "year": "2020"},
            ],
            "certifications": ["AWS Certified Developer", "Docker Certified Associate"],
            "github": "https://github.com/johndoe",
        },
        {
            "filename": "jane_smith_datasci.pdf",
            "name": "Jane Smith",
            "email": "jane.smith@email.com",
            "phone": "+94 71 987 6543",
            "summary": "Data Scientist with 3 years of experience in machine learning and statistical analysis. Strong background in Python data stack and visualization.",
            "skills": "Python, Pandas, Scikit-learn, TensorFlow, SQL, Statistics, Matplotlib, Jupyter, Data Visualization, R",
            "experience": [
                {
                    "role": "Data Scientist",
                    "company": "Analytics Hub",
                    "duration": "2022 - Present",
                    "highlights": [
                        "Built predictive models for customer churn with 92% accuracy",
                        "Automated data pipelines processing 1M+ records daily",
                        "Presented findings to C-suite executives monthly",
                    ],
                },
                {
                    "role": "Junior Data Analyst",
                    "company": "InfoTech Solutions",
                    "duration": "2021 - 2022",
                    "highlights": [
                        "Created interactive Tableau dashboards for sales team",
                        "Conducted A/B testing for product feature launches",
                    ],
                },
            ],
            "education": [
                {"degree": "MSc in Statistics", "institution": "University of Moratuwa", "year": "2021"},
                {"degree": "BSc in Mathematics", "institution": "University of Peradeniya", "year": "2019"},
            ],
            "certifications": ["Google Data Analytics Certificate"],
            "github": "https://github.com/janesmith",
        },
        {
            "filename": "alex_kumar_devops.pdf",
            "name": "Alex Kumar",
            "email": "alex.kumar@email.com",
            "phone": "+94 76 555 1234",
            "summary": "DevOps Engineer with 4 years of experience in cloud infrastructure, containerization, and CI/CD automation. Passionate about system reliability.",
            "skills": "Docker, Kubernetes, Terraform, Linux, CI/CD, AWS, Bash, Python, Ansible, Prometheus, Grafana, Jenkins",
            "experience": [
                {
                    "role": "DevOps Engineer",
                    "company": "CloudFirst Lanka",
                    "duration": "2021 - Present",
                    "highlights": [
                        "Managed Kubernetes clusters hosting 50+ microservices",
                        "Reduced infrastructure costs by 40% through optimization",
                        "Implemented monitoring stack with Prometheus and Grafana",
                    ],
                },
                {
                    "role": "System Administrator",
                    "company": "NetSoft Pvt Ltd",
                    "duration": "2020 - 2021",
                    "highlights": [
                        "Automated server provisioning with Ansible playbooks",
                        "Maintained 99.9% uptime for production servers",
                    ],
                },
            ],
            "education": [
                {"degree": "BSc in Information Technology", "institution": "SLIIT", "year": "2020"},
            ],
            "certifications": ["AWS Solutions Architect Associate", "CKA (Certified Kubernetes Administrator)"],
            "github": "https://github.com/alexkumar",
        },
        {
            "filename": "sara_silva_mobile.pdf",
            "name": "Sara Silva",
            "email": "sara.silva@email.com",
            "phone": "+94 70 222 3333",
            "summary": "Junior Mobile Developer with 1.5 years of experience in cross-platform app development using Flutter. Quick learner with a passion for UI design.",
            "skills": "Flutter, Dart, Firebase, Git, REST APIs, Figma, SQLite, Agile, Java",
            "experience": [
                {
                    "role": "Mobile Developer Intern (then Junior)",
                    "company": "AppFactory",
                    "duration": "2023 - Present",
                    "highlights": [
                        "Developed 3 Flutter apps published to Google Play Store",
                        "Integrated Firebase authentication and Firestore database",
                        "Collaborated with UX team using Figma designs",
                    ],
                },
            ],
            "education": [
                {"degree": "BSc in Software Engineering", "institution": "SLIIT", "year": "2023"},
            ],
            "certifications": [],
            "github": "NOT_FOUND",
        },
    ]

    for resume_data in resumes:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        # Header - Name
        pdf.set_font("Helvetica", "B", 18)
        pdf.cell(0, 10, resume_data["name"], new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")

        # Contact info
        pdf.set_font("Helvetica", "", 10)
        contact: str = f"{resume_data['email']} | {resume_data['phone']}"
        if resume_data.get("github") and resume_data["github"] != "NOT_FOUND":
            contact += f" | {resume_data['github']}"
        pdf.cell(0, 6, contact, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        pdf.ln(4)

        # Horizontal line
        pdf.set_draw_color(0, 0, 0)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(4)

        # Summary
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "PROFESSIONAL SUMMARY", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 5, resume_data["summary"])
        pdf.ln(3)

        # Skills
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "TECHNICAL SKILLS", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 5, resume_data["skills"])
        pdf.ln(3)

        # Experience
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "WORK EXPERIENCE", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        for exp in resume_data["experience"]:
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 6, f"{exp['role']} - {exp['company']}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("Helvetica", "I", 10)
            pdf.cell(0, 5, exp["duration"], new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("Helvetica", "", 10)
            for highlight in exp["highlights"]:
                pdf.cell(0, 5, f"    - {highlight}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(2)

        # Education
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "EDUCATION", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        for edu in resume_data["education"]:
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(0, 5, f"{edu['degree']} - {edu['institution']} ({edu['year']})", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(2)

        # Certifications
        if resume_data["certifications"]:
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 8, "CERTIFICATIONS", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("Helvetica", "", 10)
            for cert in resume_data["certifications"]:
                pdf.cell(0, 5, f"- {cert}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Save
        file_path: str = os.path.join(output_dir, resume_data["filename"])
        pdf.output(file_path)
        created_files.append(file_path)
        print(f"  Created resume: {file_path}")

    return created_files


def create_sample_flyers(output_dir: str = "data/sample_flyers") -> list[str]:
    """Create sample PDF job flyers for testing.

    Args:
        output_dir: Directory to save the sample flyers.

    Returns:
        list[str]: Paths to the created flyer files.
    """
    os.makedirs(output_dir, exist_ok=True)
    created_files: list[str] = []

    flyers: list[dict] = [
        {
            "filename": "flyer_senior_fullstack.pdf",
            "title": "We are Hiring: Senior Full-Stack Developer",
            "department": "Engineering",
            "description": (
                "Join our growing Engineering team! We need a Senior Full-Stack Developer "
                "to design and build scalable web applications. You will lead feature development, "
                "mentor juniors, and drive architectural decisions."
            ),
            "required_skills": [
                "Python", "React.js", "PostgreSQL", "Docker", "Git", "REST APIs"
            ],
            "preferred_skills": [
                "Kubernetes", "TypeScript", "GraphQL", "CI/CD"
            ],
            "experience": "4+ years",
            "education": "Bachelors in Computer Science or related field",
            "salary": "LKR 800,000 - 1,200,000 per annum",
            "deadline": "May 30, 2026",
        },
    ]

    for flyer_data in flyers:
        pdf = FPDF()
        pdf.add_page()

        # Title
        pdf.set_font("Helvetica", "B", 22)
        pdf.set_text_color(0, 51, 153)
        pdf.multi_cell(0, 12, flyer_data["title"], align="C")
        pdf.ln(5)

        # Department
        pdf.set_font("Helvetica", "I", 12)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 8, f"Department: {flyer_data['department']}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        pdf.ln(5)

        # Line
        pdf.set_draw_color(0, 51, 153)
        pdf.set_line_width(0.5)
        pdf.line(20, pdf.get_y(), 190, pdf.get_y())
        pdf.ln(8)

        # Description
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, "About the Role", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", "", 11)
        pdf.multi_cell(0, 6, flyer_data["description"])
        pdf.ln(5)

        # Required Skills
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, "Required Skills", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", "", 11)
        for skill in flyer_data["required_skills"]:
            pdf.cell(0, 6, f"    - {skill}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(3)

        # Preferred Skills
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, "Preferred Skills", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", "", 11)
        for skill in flyer_data["preferred_skills"]:
            pdf.cell(0, 6, f"    - {skill}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(3)

        # Requirements
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, "Requirements", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 6, f"- Experience: {flyer_data['experience']}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(0, 6, f"- Education: {flyer_data['education']}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(3)

        # Salary & Deadline
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, "Compensation", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 6, f"Salary Range: {flyer_data['salary']}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(3)

        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(200, 0, 0)
        pdf.cell(0, 8, f"Application Deadline: {flyer_data['deadline']}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")

        # Save
        file_path: str = os.path.join(output_dir, flyer_data["filename"])
        pdf.output(file_path)
        created_files.append(file_path)
        print(f"  Created flyer: {file_path}")

    return created_files


if __name__ == "__main__":
    print("Creating sample resumes...")
    resumes = create_sample_resumes()
    print(f"\nCreating sample job flyers...")
    flyers = create_sample_flyers()
    print(f"\nCreated {len(resumes)} resumes and {len(flyers)} flyers")
