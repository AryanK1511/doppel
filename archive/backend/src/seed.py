import asyncio

from src.database.mongodb.mongodb_client import mongodb_client
from src.module.agent.agent_service import AgentService

SAMPLE_RECRUITER = {
    "username": "demo_recruiter_1",
    "type": "recruiter",
    "profile": {
        "name": "Sarah Chen",
        "bio": "Senior Technical Recruiter at TechCorp specializing in AI/ML roles. Looking for passionate engineers who can build intelligent systems.",
        "role_description": "We're seeking a Senior AI Engineer to join our ML Platform team. You'll design and implement scalable machine learning systems, work with cutting-edge LLMs, and mentor junior engineers.",
        "candidate_selection_criteria": [
            "3+ years of experience with Python and ML frameworks (PyTorch, TensorFlow)",
            "Experience building production ML systems at scale",
            "Strong understanding of LLMs and transformer architectures",
            "Experience with cloud platforms (AWS, GCP, Azure)",
            "Excellent communication and collaboration skills",
            "Track record of shipping ML products",
        ],
        "deal_breakers": [
            "No production ML experience",
            "Unable to work in hybrid mode (3 days office)",
        ],
        "positive_signals": [
            "Open source contributions",
            "Published research or blog posts",
            "Experience with multi-agent systems",
        ],
        "company_context": "TechCorp is a leading AI company building the future of intelligent systems.",
        "team_context": "10-person ML Platform team working on core AI infrastructure.",
    },
}

SAMPLE_CANDIDATES = [
    {
        "username": "demo_candidate_1",
        "type": "candidate",
        "profile": {
            "personal_info": {
                "full_name": "Alex Johnson",
                "email": "alex.johnson@email.com",
                "phone": "+1 (555) 123-4567",
                "urls": [
                    {"name": "GitHub", "url": "https://github.com/alexjohnson"},
                    {"name": "LinkedIn", "url": "https://linkedin.com/in/alexjohnson"},
                ],
            },
            "professional_summary": "ML Engineer with 4 years of experience building production AI systems. Passionate about LLMs and multi-agent architectures. Currently working on scalable inference systems at a Series B startup.",
            "work_experience": [
                {
                    "job_title": "Senior ML Engineer",
                    "company_name": "AI Startup Inc",
                    "employment_type": "Full-time",
                    "location": "San Francisco, CA",
                    "start_date": "Jan 2022",
                    "end_date": "Present",
                    "currently_working": True,
                    "responsibilities": [
                        "Built and deployed LLM-based systems serving 1M+ requests/day",
                        "Designed multi-agent orchestration framework for complex workflows",
                        "Led team of 3 engineers on core ML infrastructure",
                        "Reduced inference latency by 60% through model optimization",
                    ],
                },
                {
                    "job_title": "ML Engineer",
                    "company_name": "DataTech Corp",
                    "employment_type": "Full-time",
                    "location": "Seattle, WA",
                    "start_date": "Jun 2020",
                    "end_date": "Dec 2021",
                    "currently_working": False,
                    "responsibilities": [
                        "Developed recommendation systems using collaborative filtering",
                        "Implemented A/B testing framework for ML experiments",
                        "Built data pipelines processing 10TB+ daily",
                    ],
                },
            ],
            "technical_skills": [
                "Python",
                "PyTorch",
                "TensorFlow",
                "LangChain",
                "FastAPI",
                "AWS",
                "Kubernetes",
                "PostgreSQL",
                "Redis",
                "Docker",
            ],
            "education": [
                {
                    "degree": "M.S.",
                    "field_of_study": "Computer Science",
                    "institution": "Stanford University",
                    "location": "Stanford, CA",
                    "graduation_date": "Jun 2020",
                }
            ],
            "projects": [
                {
                    "project_name": "Multi-Agent Framework",
                    "description": "Open source framework for building multi-agent AI systems. 2K+ GitHub stars.",
                    "urls": [{"name": "GitHub", "url": "https://github.com/alexjohnson/multiagent"}],
                }
            ],
            "soft_skills": ["Leadership", "Communication", "Problem-solving", "Mentoring"],
            "career_goals": {
                "short_term": ["Lead an ML team", "Ship impactful AI products"],
                "long_term": ["Become a technical leader in AI", "Start an AI company"],
            },
            "availability": {
                "employment_status": "Currently employed",
                "available_to_start": "2 weeks notice",
                "open_to_opportunities": True,
                "preferred_employment_type": ["Full-time"],
            },
        },
    },
    {
        "username": "demo_candidate_2",
        "type": "candidate",
        "profile": {
            "personal_info": {
                "full_name": "Maya Patel",
                "email": "maya.patel@email.com",
                "phone": "+1 (555) 987-6543",
                "urls": [
                    {"name": "GitHub", "url": "https://github.com/mayapatel"},
                    {"name": "LinkedIn", "url": "https://linkedin.com/in/mayapatel"},
                ],
            },
            "professional_summary": "Backend engineer transitioning to ML. 3 years of experience building scalable systems. Self-taught in ML through online courses and personal projects.",
            "work_experience": [
                {
                    "job_title": "Software Engineer",
                    "company_name": "WebScale Inc",
                    "employment_type": "Full-time",
                    "location": "Austin, TX",
                    "start_date": "Mar 2021",
                    "end_date": "Present",
                    "currently_working": True,
                    "responsibilities": [
                        "Built microservices handling 500K+ requests/minute",
                        "Implemented ML-powered search using Elasticsearch",
                        "Designed event-driven architecture for real-time processing",
                    ],
                }
            ],
            "technical_skills": [
                "Python",
                "Go",
                "PostgreSQL",
                "Kubernetes",
                "Redis",
                "scikit-learn",
                "TensorFlow",
                "AWS",
            ],
            "education": [
                {
                    "degree": "B.S.",
                    "field_of_study": "Computer Science",
                    "institution": "UT Austin",
                    "location": "Austin, TX",
                    "graduation_date": "May 2021",
                }
            ],
            "soft_skills": ["Fast learner", "Team player", "Detail-oriented"],
            "career_goals": {
                "short_term": ["Transition to ML engineering role"],
                "long_term": ["Become an ML architect"],
            },
            "availability": {
                "employment_status": "Currently employed",
                "available_to_start": "1 month notice",
                "open_to_opportunities": True,
                "preferred_employment_type": ["Full-time"],
            },
        },
    },
    {
        "username": "demo_candidate_3",
        "type": "candidate",
        "profile": {
            "personal_info": {
                "full_name": "James Wilson",
                "email": "james.wilson@email.com",
                "phone": "+1 (555) 246-8135",
                "urls": [
                    {"name": "GitHub", "url": "https://github.com/jameswilson"},
                ],
            },
            "professional_summary": "AI Research Engineer with 5 years of experience in NLP and LLMs. Published 3 papers at top conferences. Expert in transformer architectures and prompt engineering.",
            "work_experience": [
                {
                    "job_title": "AI Research Engineer",
                    "company_name": "AI Research Lab",
                    "employment_type": "Full-time",
                    "location": "New York, NY",
                    "start_date": "Aug 2019",
                    "end_date": "Present",
                    "currently_working": True,
                    "responsibilities": [
                        "Led research on efficient LLM fine-tuning techniques",
                        "Published papers at NeurIPS, ACL, and EMNLP",
                        "Built production NLP pipelines serving enterprise clients",
                        "Mentored 5 junior researchers",
                    ],
                }
            ],
            "technical_skills": [
                "Python",
                "PyTorch",
                "Transformers",
                "JAX",
                "CUDA",
                "GCP",
                "MLflow",
                "Weights & Biases",
            ],
            "education": [
                {
                    "degree": "Ph.D.",
                    "field_of_study": "Computer Science (NLP)",
                    "institution": "MIT",
                    "location": "Cambridge, MA",
                    "graduation_date": "May 2019",
                }
            ],
            "certifications": [
                {
                    "certification_name": "Google Cloud ML Engineer",
                    "issuing_organization": "Google",
                    "date": "Jan 2023",
                }
            ],
            "soft_skills": ["Research", "Technical writing", "Public speaking", "Mentoring"],
            "career_goals": {
                "short_term": ["Apply research to production systems"],
                "long_term": ["Lead AI research at a major tech company"],
            },
            "availability": {
                "employment_status": "Currently employed",
                "available_to_start": "1 month notice",
                "open_to_opportunities": True,
                "preferred_employment_type": ["Full-time"],
            },
        },
    },
]


async def seed_database():
    await mongodb_client.connect()

    agent_service = AgentService(mongodb_client)

    print("Seeding database with demo agents...")

    try:
        result = await agent_service.create_agent(
            username=SAMPLE_RECRUITER["username"],
            agent_type=SAMPLE_RECRUITER["type"],
            profile=SAMPLE_RECRUITER["profile"],
        )
        print(f"Created recruiter: {result['name']}")
    except ValueError as e:
        print(f"Recruiter already exists or error: {e}")

    for candidate in SAMPLE_CANDIDATES:
        try:
            result = await agent_service.create_agent(
                username=candidate["username"],
                agent_type=candidate["type"],
                profile=candidate["profile"],
            )
            print(f"Created candidate: {result['name']}")
        except ValueError as e:
            print(f"Candidate already exists or error: {e}")

    await mongodb_client.disconnect()
    print("Seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed_database())
