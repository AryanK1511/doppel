import asyncio
import json
from dataclasses import dataclass
from enum import IntEnum
from typing import Any, Dict, List, Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from src.common.config import settings


class ThinkingLevel(IntEnum):
    EXECUTION = 1
    TACTICAL = 2
    STRATEGIC = 3
    META_COGNITIVE = 4


@dataclass
class ThoughtSignature:
    thinking_level: ThinkingLevel
    what_learned: str
    goal_progress: Dict[str, bool]
    match_confidence: int
    next_action: str
    self_correction: Optional[str] = None
    should_conclude: bool = False
    critical_mismatch: bool = False
    cost: float = 0.0


@dataclass
class ConversationContext:
    turn_number: int
    conversation_history: List[Dict[str, str]]
    last_response: str
    remaining_goals: List[str]
    current_confidence: int
    previous_confidence: int = 50
    is_opening: bool = False


LEVEL_COSTS = {
    ThinkingLevel.EXECUTION: 0.0,
    ThinkingLevel.TACTICAL: 0.01,
    ThinkingLevel.STRATEGIC: 0.05,
    ThinkingLevel.META_COGNITIVE: 0.10,
}


class ThinkingLevelManager:
    def __init__(self, llm: ChatGoogleGenerativeAI):
        self.llm = llm

    def determine_level(self, context: ConversationContext) -> ThinkingLevel:
        if context.is_opening:
            return ThinkingLevel.EXECUTION

        if not context.last_response:
            return ThinkingLevel.EXECUTION

        confidence_delta = abs(context.current_confidence - context.previous_confidence)

        if confidence_delta >= 25:
            return ThinkingLevel.STRATEGIC

        if len(context.remaining_goals) <= 2 and context.current_confidence >= 80:
            return ThinkingLevel.STRATEGIC

        response_length = len(context.last_response.split())
        if response_length < 15:
            return ThinkingLevel.TACTICAL

        if context.turn_number >= 6:
            return ThinkingLevel.STRATEGIC

        return ThinkingLevel.TACTICAL

    async def think(
        self,
        level: ThinkingLevel,
        context: ConversationContext,
        goal_progress: Dict[str, bool],
        criteria: List[str],
    ) -> ThoughtSignature:
        if level == ThinkingLevel.EXECUTION:
            return self._execute_routine(context, goal_progress)
        elif level == ThinkingLevel.TACTICAL:
            return await self._tactical_thinking(context, goal_progress, criteria)
        elif level == ThinkingLevel.STRATEGIC:
            return await self._strategic_thinking(context, goal_progress, criteria)
        else:
            return await self._meta_cognitive_thinking(context, goal_progress, criteria)

    def _execute_routine(
        self, context: ConversationContext, goal_progress: Dict[str, bool]
    ) -> ThoughtSignature:
        return ThoughtSignature(
            thinking_level=ThinkingLevel.EXECUTION,
            what_learned="Opening conversation - gathering initial information",
            goal_progress=goal_progress,
            match_confidence=context.current_confidence,
            next_action="Ask opening question about their background",
            cost=LEVEL_COSTS[ThinkingLevel.EXECUTION],
        )

    async def _tactical_thinking(
        self,
        context: ConversationContext,
        goal_progress: Dict[str, bool],
        criteria: List[str],
    ) -> ThoughtSignature:
        unverified = [c for c, verified in goal_progress.items() if not verified]
        prompt = f"""You are analyzing a candidate's response in a recruiting conversation.

Response to analyze: "{context.last_response}"

Unverified criteria: {unverified[:3]}

Provide a brief tactical analysis in JSON format:
{{
    "what_learned": "1-2 sentence summary of what this response reveals",
    "criteria_updates": {{"criterion text": true/false}},
    "confidence_adjustment": number between -15 and +15,
    "next_action": "specific next question or topic to probe",
    "needs_clarification": true/false
}}

Be concise. Only mark criteria as true if clearly demonstrated."""

        messages = [HumanMessage(content=prompt)]
        response = await self.llm.ainvoke(messages)
        content = self._extract_text(response.content)

        try:
            data = json.loads(self._clean_json(content))
        except json.JSONDecodeError:
            data = {
                "what_learned": "Response received, continuing assessment",
                "criteria_updates": {},
                "confidence_adjustment": 0,
                "next_action": "Continue probing relevant skills",
                "needs_clarification": False,
            }

        new_progress = goal_progress.copy()
        for criterion, verified in data.get("criteria_updates", {}).items():
            if criterion in new_progress:
                new_progress[criterion] = verified

        new_confidence = max(
            0, min(100, context.current_confidence + data.get("confidence_adjustment", 0))
        )

        return ThoughtSignature(
            thinking_level=ThinkingLevel.TACTICAL,
            what_learned=data.get("what_learned", ""),
            goal_progress=new_progress,
            match_confidence=new_confidence,
            next_action=data.get("next_action", ""),
            cost=LEVEL_COSTS[ThinkingLevel.TACTICAL],
        )

    async def _strategic_thinking(
        self,
        context: ConversationContext,
        goal_progress: Dict[str, bool],
        criteria: List[str],
    ) -> ThoughtSignature:
        verified_count = sum(1 for v in goal_progress.values() if v)
        total_count = len(goal_progress)
        history_summary = "\n".join(
            [f"{m['role']}: {m['content'][:100]}..." for m in context.conversation_history[-4:]]
        )

        prompt = f"""You are conducting a strategic reassessment of a recruiting conversation.

Recent conversation:
{history_summary}

Latest response: "{context.last_response}"

Progress: {verified_count}/{total_count} criteria verified
Current confidence: {context.current_confidence}%
Turn number: {context.turn_number}

Provide strategic analysis in JSON format:
{{
    "what_learned": "key insight from this conversation stage",
    "criteria_updates": {{"criterion text": true/false}},
    "confidence_adjustment": number between -25 and +25,
    "self_correction": "any strategic pivot needed (or null)",
    "next_action": "strategic next move",
    "should_conclude": true/false,
    "critical_mismatch": true/false
}}

Consider: Is this candidate stronger/weaker than expected? Should we pivot strategy?"""

        messages = [HumanMessage(content=prompt)]
        response = await self.llm.ainvoke(messages)
        content = self._extract_text(response.content)

        try:
            data = json.loads(self._clean_json(content))
        except json.JSONDecodeError:
            data = {
                "what_learned": "Strategic assessment in progress",
                "criteria_updates": {},
                "confidence_adjustment": 0,
                "self_correction": None,
                "next_action": "Continue strategic assessment",
                "should_conclude": False,
                "critical_mismatch": False,
            }

        new_progress = goal_progress.copy()
        for criterion, verified in data.get("criteria_updates", {}).items():
            if criterion in new_progress:
                new_progress[criterion] = verified

        new_confidence = max(
            0, min(100, context.current_confidence + data.get("confidence_adjustment", 0))
        )

        return ThoughtSignature(
            thinking_level=ThinkingLevel.STRATEGIC,
            what_learned=data.get("what_learned", ""),
            goal_progress=new_progress,
            match_confidence=new_confidence,
            next_action=data.get("next_action", ""),
            self_correction=data.get("self_correction"),
            should_conclude=data.get("should_conclude", False),
            critical_mismatch=data.get("critical_mismatch", False),
            cost=LEVEL_COSTS[ThinkingLevel.STRATEGIC],
        )

    async def _meta_cognitive_thinking(
        self,
        context: ConversationContext,
        goal_progress: Dict[str, bool],
        criteria: List[str],
    ) -> ThoughtSignature:
        history_summary = "\n".join(
            [f"{m['role']}: {m['content']}" for m in context.conversation_history]
        )

        prompt = f"""You are conducting deep meta-cognitive reflection on a recruiting conversation.

Full conversation:
{history_summary}

Latest response: "{context.last_response}"

Current assessment:
- Verified criteria: {[c for c, v in goal_progress.items() if v]}
- Unverified: {[c for c, v in goal_progress.items() if not v]}
- Confidence: {context.current_confidence}%

Provide deep reflection in JSON format:
{{
    "what_learned": "fundamental insight about this candidate/conversation",
    "criteria_updates": {{"criterion text": true/false}},
    "confidence_adjustment": number between -40 and +40,
    "self_correction": "critical reframing of approach (if needed)",
    "next_action": "final action to take",
    "should_conclude": true/false,
    "critical_mismatch": true/false,
    "learning_for_future": "pattern to remember for future conversations"
}}

This is expensive thinking - provide deep, actionable insights."""

        messages = [HumanMessage(content=prompt)]
        response = await self.llm.ainvoke(messages)
        content = self._extract_text(response.content)

        try:
            data = json.loads(self._clean_json(content))
        except json.JSONDecodeError:
            data = {
                "what_learned": "Deep reflection completed",
                "criteria_updates": {},
                "confidence_adjustment": 0,
                "self_correction": None,
                "next_action": "Conclude conversation",
                "should_conclude": True,
                "critical_mismatch": False,
            }

        new_progress = goal_progress.copy()
        for criterion, verified in data.get("criteria_updates", {}).items():
            if criterion in new_progress:
                new_progress[criterion] = verified

        new_confidence = max(
            0, min(100, context.current_confidence + data.get("confidence_adjustment", 0))
        )

        return ThoughtSignature(
            thinking_level=ThinkingLevel.META_COGNITIVE,
            what_learned=data.get("what_learned", ""),
            goal_progress=new_progress,
            match_confidence=new_confidence,
            next_action=data.get("next_action", ""),
            self_correction=data.get("self_correction"),
            should_conclude=data.get("should_conclude", True),
            critical_mismatch=data.get("critical_mismatch", False),
            cost=LEVEL_COSTS[ThinkingLevel.META_COGNITIVE],
        )

    def _extract_text(self, content) -> str:
        if isinstance(content, list):
            parts = []
            for part in content:
                if isinstance(part, dict) and "text" in part:
                    parts.append(part["text"])
                elif isinstance(part, str):
                    parts.append(part)
            return " ".join(parts)
        return str(content)

    def _clean_json(self, text: str) -> str:
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()


recruiter_profile = {
    "name": "Brodie Moss",
    "bio": "Senior Technical Recruiter at RBC specializing in Platform Technology and RBCx digital solutions. Focused on finding developers who can bridge technical excellence with user experience.",
    "candidate_selection_criteria": [
        "Minimum 4 years of hands-on experience with PHP, JavaScript, and WordPress VIP",
        "Strong proficiency with modern frontend tools including Figma and Tailwind CSS",
        "Demonstrated experience building accessible (WCAG AA compliant) web applications",
        "Proven track record with RESTful API design, development, and troubleshooting",
        "Solid understanding of DevOps practices using Git, Jenkins, Jira, and CI/CD pipelines",
        "Experience translating UI/UX designs into pixel-perfect, responsive interfaces",
        "Ability to write clean, testable, efficient code following software development best practices",
        "Strong problem-solving skills with attention to detail",
        "Experience building reusable PHP templates and scalable component architectures",
        "Bonus: Experience with CRM integrations (HubSpot, Salesforce) and performance-optimized web animations",
        "Collaborative mindset with ability to work in agile, high-performing teams",
        "Passion for creating customer-focused, engaging applications",
    ],
    "job_description": "We are looking for a Software Developer with 4+ years of experience in PHP, JavaScript, WordPress VIP, and modern frontend technologies to join our Platform Technology team at RBCx. The ideal candidate excels at translating designs into accessible, responsive web interfaces while maintaining strong DevOps practices and architectural excellence.",
}

candidate_profile = {
    # Basic Information
    "personal_info": {
        "full_name": "Aryan Khurana",
        "email": "aryan.khurana@gmail.com",
        "phone": "+1 (647) 555-0142",
        "location": {"city": "Toronto", "province": "Ontario", "country": "Canada"},
        "linkedin_url": "linkedin.com/in/aryankhurana",
        "github_url": "github.com/aryankhurana",
        "portfolio_url": "rezzy.dev",
        "age": 22,
    },
    # Professional Summary
    "professional_summary": "AI Application Developer at RBC with expertise in building intelligent automation solutions using multi-agent systems, FastAPI, and modern web technologies. Founder of Fuselabs, a consulting firm generating $4K monthly revenue through AI automation services. Passionate about production-ready AI implementations and advanced technical architectures.",
    # Work Experience
    "work_experience": [
        {
            "job_title": "AI Application Developer",
            "company_name": "RBC",
            "employment_type": "Full-time",
            "location": "Toronto, ON",
            "start_date": "June 2023",
            "end_date": "Present",
            "currently_working": True,
            "responsibilities": [
                "Develop AI-powered applications and automation solutions for enterprise banking systems",
                "Build and maintain multi-agent systems for complex workflow automation",
                "Design and implement RESTful APIs using FastAPI and MongoDB",
                "Collaborate with cross-functional teams to deliver strategic initiatives",
                "Research and adopt emerging AI technologies to keep products up-to-date",
            ],
            "technologies_used": [
                "Python",
                "FastAPI",
                "MongoDB",
                "AI/ML",
                "Multi-agent systems",
                "RESTful APIs",
            ],
            "achievements": [
                "Successfully deployed AI automation solutions serving multiple business functions",
                "Implemented scalable multi-agent architectures for enterprise applications",
            ],
        },
        {
            "job_title": "Founder & AI Consultant",
            "company_name": "Fuselabs",
            "employment_type": "Self-employed",
            "location": "Toronto, ON",
            "start_date": "January 2023",
            "end_date": "Present",
            "currently_working": True,
            "responsibilities": [
                "Provide AI automation and custom development services to clients",
                "Design and architect full-stack AI solutions using FastAPI and MongoDB",
                "Build production-ready applications with focus on scalability and performance",
                "Manage client relationships and project delivery timelines",
                "Develop custom AI automation workflows for business process optimization",
            ],
            "technologies_used": [
                "Python",
                "FastAPI",
                "MongoDB",
                "JavaScript",
                "AI/ML",
                "Full-stack Development",
            ],
            "achievements": [
                "Generated $4,000 monthly recurring revenue through consulting services",
                "Built strong client base through professor connections and referrals",
                "Delivered multiple successful AI automation projects",
            ],
        },
        {
            "job_title": "Software Developer Fellow",
            "company_name": "MLH Fellowship",
            "employment_type": "Contract",
            "location": "Remote",
            "start_date": "September 2022",
            "end_date": "December 2022",
            "currently_working": False,
            "responsibilities": [
                "Collaborated on open-source projects with global developer community",
                "Developed software solutions using modern development practices",
                "Participated in code reviews and technical discussions",
            ],
            "technologies_used": ["Python", "JavaScript", "Git", "Agile"],
            "achievements": [
                "Contributed to 3 major open-source projects",
                "Completed fellowship with distinction",
            ],
        },
        {
            "job_title": "Research Developer",
            "company_name": "Seneca Research",
            "employment_type": "Contract",
            "location": "Toronto, ON",
            "start_date": "May 2022",
            "end_date": "August 2022",
            "currently_working": False,
            "responsibilities": [
                "Conducted research and development on technical projects",
                "Implemented proof-of-concept solutions for research initiatives",
                "Collaborated with research team on technical implementations",
            ],
            "technologies_used": ["Python", "Research methodologies", "Data analysis"],
            "achievements": [
                "Published research findings in internal reports",
                "Developed 2 proof-of-concept prototypes",
            ],
        },
    ],
    # Education
    "education": [
        {
            "degree": "Bachelor of Science",
            "field_of_study": "Computer Science",
            "institution": "Seneca College of Applied Arts and Technology",
            "location": "Toronto, ON",
            "graduation_date": "April 2024",
            "gpa": "3.8/4.0",
            "relevant_coursework": [
                "Artificial Intelligence",
                "Software Engineering",
                "Database Systems",
                "Web Development",
                "Algorithms and Data Structures",
                "Machine Learning",
                "Cloud Computing",
            ],
        }
    ],
    # Technical Skills
    "technical_skills": {
        "programming_languages": {
            "proficient": ["Python", "JavaScript"],
            "intermediate": ["PHP", "HTML", "CSS"],
            "basic": ["Java", "C++"],
        },
        "frameworks_libraries": {
            "backend": ["FastAPI", "Flask", "Django"],
            "frontend": ["React", "Vue.js", "Modern JavaScript"],
            "ai_ml": ["CrewAI", "LangChain", "TensorFlow", "PyTorch"],
            "other": ["MoviePy", "Pandas", "NumPy"],
        },
        "databases": ["MongoDB", "PostgreSQL", "MySQL", "Redis"],
        "ai_ml_expertise": [
            "Multi-agent systems",
            "AI automation",
            "LLM integration",
            "Prompt engineering",
            "Voice cloning",
            "Video reasoning",
            "Avatar generation",
            "Natural Language Processing",
            "Computer Vision",
        ],
        "web_technologies": [
            "RESTful APIs",
            "API design and development",
            "Modern web development",
            "Responsive design principles",
            "WebSockets",
            "GraphQL",
        ],
        "devops_tools": [
            "Git",
            "GitHub",
            "GitLab",
            "CI/CD pipelines",
            "Docker",
            "Jenkins",
            "GitHub Actions",
        ],
        "design_tools": ["Figma", "Adobe XD", "Sketch"],
        "other_tools": ["Jira", "Confluence", "Postman", "VS Code", "PyCharm"],
    },
    # Projects & Portfolio
    "projects": [
        {
            "project_name": "Viralens",
            "status": "In Active Development",
            "project_url": "viralens.app",
            "github_url": "github.com/aryankhurana/viralens",
            "start_date": "November 2025",
            "end_date": "Ongoing (Hackathon deadline: February 9, 2026)",
            "short_description": "AI-powered social media content creation platform using multi-agent collaboration",
            "detailed_description": "Automated social media content creation platform that uses AI agents to collaborate like a real team, generating Instagram Reels and TikTok content. Features include voice cloning, avatar generation, subtitle automation, and autonomous performance learning loops that analyze social media metrics to self-improve content strategies.",
            "technologies_used": [
                "Google A2A Protocol",
                "CrewAI",
                "Multi-agent systems",
                "Python",
                "FastAPI",
                "MongoDB",
                "Voice cloning AI",
                "Avatar generation",
                "MoviePy",
                "OpenAI API",
                "Gemini API",
            ],
            "role": "Solo Developer / Architect",
            "key_features": [
                "Multi-agent collaboration system mimicking real team dynamics",
                "Autonomous performance learning from social media metrics",
                "Voice cloning for consistent audio branding",
                "Automated subtitle generation and synchronization",
                "AI-powered avatar generation for video content",
                "Self-improving content strategy algorithms",
                "Integration with Instagram and TikTok APIs",
                "Real-time analytics dashboard",
            ],
            "achievements": [
                "Gemini 3 Hackathon entry ($100,000 prize pool)",
                "Advanced multi-agent architecture implementation",
                "Production-ready automation pipeline",
                "Processed 500+ test videos through the pipeline",
            ],
        },
        {
            "project_name": "AI Security Camera System",
            "status": "In Development",
            "project_url": "",
            "github_url": "github.com/aryankhurana/ai-security-cam",
            "start_date": "September 2025",
            "end_date": "Ongoing",
            "short_description": "Intelligent security guard system using video reasoning",
            "detailed_description": "AI-powered security camera project that functions as an intelligent security guard, using video reasoning to predict threats and provide conversational responses to security events.",
            "technologies_used": [
                "Python",
                "OpenCV",
                "YOLOv8",
                "Computer Vision",
                "Threat detection algorithms",
                "GPT-4 Vision API",
                "Real-time processing",
                "WebRTC",
                "FastAPI",
            ],
            "role": "Solo Developer",
            "key_features": [
                "Real-time video threat analysis",
                "Predictive threat detection using machine learning",
                "Conversational interface for security responses",
                "Video reasoning capabilities with GPT-4 Vision",
                "Motion detection and tracking",
                "Facial recognition integration",
                "Alert notification system",
                "Cloud storage integration",
            ],
            "achievements": [
                "Achieved 85% accuracy in threat detection",
                "Real-time processing at 30 FPS",
                "Deployed beta version for testing",
            ],
        },
        {
            "project_name": "Rezzy",
            "status": "Live/Production",
            "project_url": "rezzy.dev",
            "github_url": "github.com/aryankhurana/rezzy",
            "start_date": "August 2024",
            "end_date": "Ongoing maintenance",
            "short_description": "AI-powered resume builder with intelligent optimization",
            "detailed_description": "Resume builder tool offering free and Pro features for automated resume generation and optimization. Uses AI prompts that mimic recruiter decision-making for strategic resume analysis and cover letter generation, rather than simple keyword optimization.",
            "technologies_used": [
                "Python",
                "FastAPI",
                "React",
                "MongoDB",
                "OpenAI GPT-4",
                "Prompt engineering",
                "Stripe API",
                "AWS S3",
                "Tailwind CSS",
            ],
            "role": "Founder / Lead Developer",
            "key_features": [
                "AI-powered resume analysis and scoring",
                "Strategic cover letter generation",
                "Recruiter-mimicking decision algorithms",
                "Free and Pro tier features",
                "Resume optimization beyond keyword matching",
                "ATS compatibility checker",
                "Multiple template options",
                "PDF export functionality",
            ],
            "achievements": [
                "Live production application serving 2,500+ users",
                "Innovative approach to resume optimization using AI",
                "Generated $800 MRR from Pro subscriptions",
                "4.7/5 star rating from users",
                "Featured on Product Hunt",
            ],
        },
    ],
    # Certifications & Awards
    "certifications": [
        {
            "certification_name": "AWS Certified Cloud Practitioner",
            "issuing_organization": "Amazon Web Services",
            "date": "August 2023",
        },
        {
            "certification_name": "MongoDB Developer Certification",
            "issuing_organization": "MongoDB University",
            "date": "May 2023",
        },
    ],
    "awards_achievements": [
        {
            "title": "Gemini 3 Hackathon Participant",
            "issuer": "Google Developer Groups",
            "date": "January 2026",
            "description": "Competing with Viralens project in $100,000 prize pool hackathon",
        },
        {
            "title": "Dean's List",
            "issuer": "Seneca College",
            "date": "April 2023",
            "description": "Academic excellence recognition for maintaining GPA above 3.75",
        },
        {
            "title": "Best Innovation Award",
            "issuer": "Seneca Hackathon 2023",
            "date": "March 2023",
            "description": "First place for innovative AI solution in college hackathon",
        },
    ],
    # Soft Skills
    "soft_skills": [
        "Strategic thinking and planning",
        "Problem-solving",
        "Self-directed learning",
        "Entrepreneurial mindset",
        "Client relationship management",
        "Technical architecture design",
        "Time management",
        "Productivity optimization",
        "Written and verbal communication",
        "Attention to detail",
        "Analytical thinking",
        "Adaptability",
        "Leadership",
        "Collaboration",
        "Critical thinking",
    ],
    # Languages
    "languages": [
        {"language": "English", "proficiency": "Native/Fluent"},
        {"language": "Hindi", "proficiency": "Conversational"},
        {"language": "Punjabi", "proficiency": "Basic"},
    ],
    # Social Media & Online Presence
    "social_media": {
        "instagram": {
            "handle": "@aryan.builds",
            "followers": 4000,
            "content_focus": "Tech/AI content creation, coding tutorials, entrepreneurship",
        },
        "twitter": {
            "handle": "@aryankhurana_",
            "followers": 850,
            "content_focus": "AI developments, tech insights",
        },
        "personal_website": "rezzy.dev",
        "blog": "medium.com/@aryankhurana",
        "youtube": {
            "channel": "Aryan Codes",
            "subscribers": 1200,
            "content_focus": "AI tutorials, project walkthroughs",
        },
    },
    # Professional Interests
    "professional_interests": [
        "Artificial Intelligence and Machine Learning",
        "Multi-agent architectures",
        "AI automation and workflow optimization",
        "Production-ready implementations",
        "Advanced technical concepts and system design",
        "Emerging AI technologies (LLMs, Vision models)",
        "Content creation with AI",
        "Entrepreneurship and SaaS development",
        "Developer tools and productivity",
        "FinTech and banking technology",
    ],
    # Hobbies & Personal Interests
    "hobbies": [
        "eFootball gaming (competitive player)",
        "Content creation and video editing",
        "Following AI/tech trends and research papers",
        "Strategic planning and productivity optimization",
        "Photography",
        "Traveling",
        "Fitness and workout routines",
        "Reading tech blogs and newsletters",
    ],
    # Career Goals
    "career_goals": {
        "short_term": [
            "Win Gemini 3 Hackathon with Viralens platform",
            "Scale Fuselabs consulting revenue to $10K+/month",
            "Master advanced multi-agent architectures and AI orchestration",
            "Balance full-time work with entrepreneurial ventures effectively",
            "Launch Viralens as a commercial product post-hackathon",
        ],
        "long_term": [
            "Build successful AI product company valued at $10M+",
            "Become recognized expert in multi-agent systems and AI automation",
            "Create impactful AI solutions at scale serving 100K+ users",
            "Grow Fuselabs into established consultancy with team of 10+",
            "Speak at major AI/tech conferences",
            "Contribute to open-source AI frameworks",
            "Mentor aspiring AI developers and entrepreneurs",
        ],
    },
    # Work Preferences
    "work_preferences": {
        "preferred_role_types": [
            "AI Developer",
            "Software Engineer",
            "Full-stack Developer",
            "AI Consultant",
            "Technical Lead",
        ],
        "preferred_industries": [
            "Technology",
            "AI/ML",
            "FinTech",
            "SaaS",
            "Startup ecosystem",
        ],
        "work_environment": ["Hybrid", "Remote"],
        "company_size": [
            "Startup (1-50)",
            "Medium (50-500)",
            "Large Enterprise (500+)",
        ],
        "willing_to_relocate": False,
        "salary_expectations": {"minimum": "$85,000 CAD", "preferred": "$110,000 CAD"},
    },
    # Availability
    "availability": {
        "employment_status": "Currently employed",
        "available_to_start": "2 weeks notice",
        "open_to_opportunities": True,
        "preferred_employment_type": ["Full-time", "Contract"],
    },
    # Additional Information
    "additional_info": {
        "work_style": [
            "Prefers sophisticated solutions over simplified prototypes",
            "Focus on production-ready implementations and scalability",
            "Deep understanding of complex technical concepts",
            "Hands-on coding and architecture approach",
            "Continuous learning and adoption of emerging technologies",
            "Agile methodology advocate",
            "Strong documentation practices",
            "Test-driven development when applicable",
        ],
        "notable_mentions": [
            "Generates $4,000/month through consulting side business while working full-time",
            "Active hackathon participant with focus on high-impact projects",
            "Strong focus on AI and automation technologies",
            "Entrepreneurial experience with multiple live projects",
            "Built and scaled Rezzy to 2,500+ users independently",
            "Instagram content creator with 4,000 engaged followers",
            "Self-taught in advanced AI concepts and multi-agent systems",
        ],
        "volunteering": [
            {
                "organization": "Code for Canada",
                "role": "Mentor",
                "duration": "January 2024 to Present",
                "description": "Mentoring junior developers in AI/ML and web development",
            }
        ],
        "publications": [
            {
                "title": "Building Production-Ready Multi-Agent Systems: A Practical Guide",
                "publication": "Medium",
                "date": "December 2025",
                "url": "medium.com/@aryankhurana/multi-agent-systems",
            }
        ],
    },
    # References
    "references": [
        {
            "name": "Dr. Sarah Johnson",
            "relationship": "Former Professor",
            "company": "Seneca College",
            "position": "Computer Science Professor",
            "email": "sarah.johnson@senecacollege.ca",
            "phone": "+1 (416) 555-0198",
        },
        {
            "name": "Michael Chen",
            "relationship": "Client",
            "company": "TechStart Inc.",
            "position": "CTO",
            "email": "michael.chen@techstart.com",
            "phone": "+1 (647) 555-0234",
        },
    ],
}


class RecruiterAgent:
    def __init__(self, profile: dict, llm: ChatGoogleGenerativeAI):
        self.profile = profile
        self.llm = llm
        self.name = profile["name"]
        self.criteria = profile["candidate_selection_criteria"]
        self.match_confidence = 50
        self.goal_progress: Dict[str, bool] = {c: False for c in self.criteria}
        self.thought_signatures: List[ThoughtSignature] = []
        self.thinking_manager = ThinkingLevelManager(llm)
        self._build_system_prompt()

    def _build_system_prompt(self):
        criteria_list = "\n".join(
            [f"{i + 1}. {criterion}" for i, criterion in enumerate(self.criteria)]
        )

        self.system_prompt = f"""You are {self.profile["name"]}, {self.profile["bio"]}

You're at a networking event having a casual conversation with a candidate. Keep it brief, natural, and conversational - like a quick chat at a career fair.

Job: {self.profile["job_description"]}

Selection Criteria (mentally check off as you learn):
{criteria_list}

Guidelines:
- Keep responses SHORT (2-4 sentences max for questions, 1-2 sentences for follow-ups)
- Ask one question at a time
- Be friendly but direct - no long explanations
- After 6-10 exchanges, wrap up with a final evaluation
- Final evaluation format:
  ✓/✗ for each criterion with brief evidence
  Rating: X/10
  Decision: GOOD FIT or NOT A FIT with 2-3 sentence reasoning

Keep it natural and brief - this is a quick networking chat, not a formal interview."""

    def get_remaining_goals(self) -> List[str]:
        return [c for c, verified in self.goal_progress.items() if not verified]

    async def reflect_on_response(
        self, context: ConversationContext
    ) -> ThoughtSignature:
        level = self.thinking_manager.determine_level(context)
        signature = await self.thinking_manager.think(
            level, context, self.goal_progress, self.criteria
        )
        self.thought_signatures.append(signature)
        self.goal_progress = signature.goal_progress
        self.match_confidence = signature.match_confidence
        return signature

    async def respond(self, conversation_history: List[Dict[str, str]]) -> str:
        messages = [SystemMessage(content=self.system_prompt)]

        if not conversation_history:
            messages.append(
                HumanMessage(
                    content="Start the conversation with a friendly greeting and ask what brings them to the networking event."
                )
            )
        else:
            for msg in conversation_history:
                if msg["role"] == "recruiter":
                    messages.append(AIMessage(content=msg["content"]))
                elif msg["role"] == "candidate":
                    messages.append(HumanMessage(content=msg["content"]))

        response = await self.llm.ainvoke(messages)
        return self._extract_text(response.content)

    async def respond_with_signature(
        self, conversation_history: List[Dict[str, str]], latest_signature: ThoughtSignature
    ) -> str:
        messages = [SystemMessage(content=self.system_prompt)]

        for msg in conversation_history:
            if msg["role"] == "recruiter":
                messages.append(AIMessage(content=msg["content"]))
            elif msg["role"] == "candidate":
                messages.append(HumanMessage(content=msg["content"]))

        guidance = f"""Based on your analysis:
- You learned: {latest_signature.what_learned}
- Your next action should be: {latest_signature.next_action}
- Current confidence in this candidate: {latest_signature.match_confidence}%
{"- Self-correction: " + latest_signature.self_correction if latest_signature.self_correction else ""}

Generate your next response accordingly. Keep it natural and conversational."""

        messages.append(HumanMessage(content=guidance))
        response = await self.llm.ainvoke(messages)
        return self._extract_text(response.content)

    async def generate_final_evaluation(
        self, conversation_history: List[Dict[str, str]]
    ) -> str:
        verified = [c for c, v in self.goal_progress.items() if v]
        unverified = [c for c, v in self.goal_progress.items() if not v]

        messages = [SystemMessage(content=self.system_prompt)]
        for msg in conversation_history:
            if msg["role"] == "recruiter":
                messages.append(AIMessage(content=msg["content"]))
            elif msg["role"] == "candidate":
                messages.append(HumanMessage(content=msg["content"]))

        eval_prompt = f"""Provide your final evaluation now.

Your assessment so far:
- Match confidence: {self.match_confidence}%
- Verified criteria: {len(verified)}/{len(self.criteria)}
- Verified: {verified[:5]}
- Not verified: {unverified[:5]}

Format:
✓/✗ for each criterion with brief evidence
Rating: X/10
Decision: GOOD FIT or NOT A FIT with 2-3 sentence reasoning"""

        messages.append(HumanMessage(content=eval_prompt))
        response = await self.llm.ainvoke(messages)
        return self._extract_text(response.content)

    def _extract_text(self, content) -> str:
        if isinstance(content, list):
            parts = []
            for part in content:
                if isinstance(part, dict) and "text" in part:
                    parts.append(part["text"])
                elif isinstance(part, str):
                    parts.append(part)
            return " ".join(parts) if parts else str(content)
        return str(content)


class CandidateAgent:
    def __init__(self, profile: dict, llm: ChatGoogleGenerativeAI):
        self.profile = profile
        self.llm = llm
        self.name = profile["personal_info"]["full_name"]
        self.presentation_goals = [
            "Highlight relevant strengths",
            "Address skill gaps honestly",
            "Show enthusiasm and culture fit",
        ]
        self.thought_signatures: List[ThoughtSignature] = []
        self._build_system_prompt()

    def _build_system_prompt(self):
        profile_json = json.dumps(self.profile, indent=2)

        self.system_prompt = f"""You are {self.profile["personal_info"]["full_name"]} at a networking event.

Your profile:
{profile_json}

Guidelines:
- Keep responses SHORT (2-3 sentences max)
- Be natural and conversational - like talking to someone at a career fair
- Answer questions directly, reference your actual experience when relevant
- If you don't have experience with something, briefly say so and mention related skills
- Don't over-explain or be verbose
- Stay authentic to your profile above

This is a quick networking chat, not a formal interview. Keep it brief and natural."""

    async def reflect_on_question(
        self, question: str, conversation_history: List[Dict[str, str]]
    ) -> ThoughtSignature:
        prompt = f"""You are a candidate analyzing a recruiter's question to strategize your response.

Question: "{question}"

Your profile summary:
- Current role: {self.profile.get('professional_summary', 'N/A')}
- Key skills: {list(self.profile.get('technical_skills', {}).get('programming_languages', {}).get('proficient', []))}

Analyze in JSON format:
{{
    "what_learned": "What is the recruiter probing for?",
    "strategy": "How should you frame your answer?",
    "relevant_experience": "What from your profile is most relevant?",
    "potential_gap": "Any skill gaps to address honestly?"
}}"""

        messages = [HumanMessage(content=prompt)]
        response = await self.llm.ainvoke(messages)
        content = self._extract_text(response.content)

        try:
            data = json.loads(self._clean_json(content))
        except json.JSONDecodeError:
            data = {
                "what_learned": "Recruiter is assessing my fit",
                "strategy": "Respond authentically",
                "relevant_experience": "Draw from my background",
                "potential_gap": None,
            }

        signature = ThoughtSignature(
            thinking_level=ThinkingLevel.TACTICAL,
            what_learned=data.get("what_learned", ""),
            goal_progress={g: False for g in self.presentation_goals},
            match_confidence=50,
            next_action=data.get("strategy", ""),
            cost=LEVEL_COSTS[ThinkingLevel.TACTICAL],
        )
        self.thought_signatures.append(signature)
        return signature

    async def respond(self, conversation_history: List[Dict[str, str]]) -> str:
        messages = [SystemMessage(content=self.system_prompt)]

        for msg in conversation_history:
            if msg["role"] == "recruiter":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "candidate":
                messages.append(AIMessage(content=msg["content"]))

        response = await self.llm.ainvoke(messages)
        return self._extract_text(response.content)

    async def respond_with_signature(
        self, conversation_history: List[Dict[str, str]], signature: ThoughtSignature
    ) -> str:
        messages = [SystemMessage(content=self.system_prompt)]

        for msg in conversation_history:
            if msg["role"] == "recruiter":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "candidate":
                messages.append(AIMessage(content=msg["content"]))

        guidance = f"""Based on your analysis:
- The recruiter is probing for: {signature.what_learned}
- Your strategy: {signature.next_action}

Respond naturally while following this strategy."""

        messages.append(HumanMessage(content=guidance))
        response = await self.llm.ainvoke(messages)
        return self._extract_text(response.content)

    def _extract_text(self, content) -> str:
        if isinstance(content, list):
            parts = []
            for part in content:
                if isinstance(part, dict) and "text" in part:
                    parts.append(part["text"])
                elif isinstance(part, str):
                    parts.append(part)
            return " ".join(parts) if parts else str(content)
        return str(content)

    def _clean_json(self, text: str) -> str:
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()


class ConversationOrchestrator:
    def __init__(self, recruiter: RecruiterAgent, candidate: CandidateAgent):
        self.recruiter = recruiter
        self.candidate = candidate
        self.conversation_history: List[Dict[str, str]] = []
        self.total_cost = 0.0

    def _print_message(self, speaker: str, role: str, message: str):
        print(f"\n[{speaker} - {role}]: {message}\n")

    def _print_thought_signature(self, signature: ThoughtSignature, agent_name: str):
        level_names = {
            ThinkingLevel.EXECUTION: "Execution",
            ThinkingLevel.TACTICAL: "Tactical",
            ThinkingLevel.STRATEGIC: "Strategic",
            ThinkingLevel.META_COGNITIVE: "Meta-Cognitive",
        }
        level_name = level_names.get(signature.thinking_level, "Unknown")

        verified_count = sum(1 for v in signature.goal_progress.values() if v)
        total_count = len(signature.goal_progress)

        print(f"\n{'─' * 60}")
        print(f"[THOUGHT SIGNATURE - {agent_name}] Level {signature.thinking_level}: {level_name}")
        print(f"{'─' * 60}")
        print(f"├─ Learned: {signature.what_learned[:80]}{'...' if len(signature.what_learned) > 80 else ''}")
        print(f"├─ Confidence: {signature.match_confidence}%")
        print(f"├─ Goal Progress: {verified_count}/{total_count} criteria verified")
        print(f"├─ Next Action: {signature.next_action[:60]}{'...' if len(signature.next_action) > 60 else ''}")
        if signature.self_correction:
            print(f"├─ Self-Correction: {signature.self_correction[:60]}...")
        if signature.should_conclude:
            print("├─ Decision: CONCLUDE CONVERSATION")
        if signature.critical_mismatch:
            print("├─ ⚠ CRITICAL MISMATCH DETECTED")
        print(f"└─ Cost: ${signature.cost:.3f}")
        print(f"{'─' * 60}\n")

    async def run_conversation(self, max_turns: int = 12) -> Dict[str, Any]:
        print("=" * 80)
        print("NETWORKING SESSION - SCREENING CONVERSATION WITH THOUGHT SIGNATURES")
        print("=" * 80)
        print()

        turn_count = 0
        final_eval = None

        opening_context = ConversationContext(
            turn_number=0,
            conversation_history=[],
            last_response="",
            remaining_goals=self.recruiter.get_remaining_goals(),
            current_confidence=self.recruiter.match_confidence,
            is_opening=True,
        )
        opening_signature = await self.recruiter.reflect_on_response(opening_context)
        self.total_cost += opening_signature.cost
        self._print_thought_signature(opening_signature, self.recruiter.name)

        response = await self.recruiter.respond(self.conversation_history)
        self.conversation_history.append({"role": "recruiter", "content": response})
        self._print_message(self.recruiter.name, "Recruiter", response)

        while turn_count < max_turns:
            last_recruiter_msg = self.conversation_history[-1]["content"]
            candidate_signature = await self.candidate.reflect_on_question(
                last_recruiter_msg, self.conversation_history
            )
            self.total_cost += candidate_signature.cost
            self._print_thought_signature(candidate_signature, self.candidate.name)

            candidate_response = await self.candidate.respond_with_signature(
                self.conversation_history, candidate_signature
            )
            self.conversation_history.append(
                {"role": "candidate", "content": candidate_response}
            )
            self._print_message(self.candidate.name, "Candidate", candidate_response)
            turn_count += 1

            previous_confidence = self.recruiter.match_confidence
            context = ConversationContext(
                turn_number=turn_count,
                conversation_history=self.conversation_history,
                last_response=candidate_response,
                remaining_goals=self.recruiter.get_remaining_goals(),
                current_confidence=self.recruiter.match_confidence,
                previous_confidence=previous_confidence,
            )

            recruiter_signature = await self.recruiter.reflect_on_response(context)
            self.total_cost += recruiter_signature.cost
            self._print_thought_signature(recruiter_signature, self.recruiter.name)

            if recruiter_signature.should_conclude or recruiter_signature.critical_mismatch:
                final_eval = await self.recruiter.generate_final_evaluation(
                    self.conversation_history
                )
                self.conversation_history.append(
                    {"role": "recruiter", "content": final_eval}
                )
                self._print_message(self.recruiter.name, "Recruiter", final_eval)
                break

            if turn_count >= max_turns - 1:
                final_eval = await self.recruiter.generate_final_evaluation(
                    self.conversation_history
                )
                self.conversation_history.append(
                    {"role": "recruiter", "content": final_eval}
                )
                self._print_message(self.recruiter.name, "Recruiter", final_eval)
                break

            recruiter_response = await self.recruiter.respond_with_signature(
                self.conversation_history, recruiter_signature
            )
            self.conversation_history.append(
                {"role": "recruiter", "content": recruiter_response}
            )
            self._print_message(self.recruiter.name, "Recruiter", recruiter_response)

        if not final_eval:
            final_eval = await self.recruiter.generate_final_evaluation(
                self.conversation_history
            )
            self._print_message(self.recruiter.name, "Recruiter", final_eval)

        print("\n" + "=" * 80)
        print("CONVERSATION COMPLETE")
        print("=" * 80)
        self._print_summary()

        return {
            "conversation_history": self.conversation_history,
            "final_evaluation": final_eval,
            "recruiter_signatures": self.recruiter.thought_signatures,
            "candidate_signatures": self.candidate.thought_signatures,
            "final_confidence": self.recruiter.match_confidence,
            "total_cost": self.total_cost,
        }

    def _print_summary(self):
        print("\n" + "=" * 80)
        print("THOUGHT SIGNATURE SUMMARY")
        print("=" * 80)

        level_counts = {level: 0 for level in ThinkingLevel}
        for sig in self.recruiter.thought_signatures:
            level_counts[sig.thinking_level] += 1

        print("\nRecruiter Thinking Levels Used:")
        for level, count in level_counts.items():
            level_names = {
                ThinkingLevel.EXECUTION: "Execution (L1)",
                ThinkingLevel.TACTICAL: "Tactical (L2)",
                ThinkingLevel.STRATEGIC: "Strategic (L3)",
                ThinkingLevel.META_COGNITIVE: "Meta-Cognitive (L4)",
            }
            if count > 0:
                print(f"  {level_names[level]}: {count} times")

        verified = sum(1 for v in self.recruiter.goal_progress.values() if v)
        total = len(self.recruiter.goal_progress)
        print("\nFinal Assessment:")
        print(f"  Criteria Verified: {verified}/{total}")
        print(f"  Final Confidence: {self.recruiter.match_confidence}%")
        print(f"  Total API Cost: ${self.total_cost:.3f}")
        print("=" * 80)


async def main():
    llm = ChatGoogleGenerativeAI(
        model="gemini-3-flash-preview",
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0.8,
    )

    recruiter = RecruiterAgent(recruiter_profile, llm)
    candidate = CandidateAgent(candidate_profile, llm)
    orchestrator = ConversationOrchestrator(recruiter, candidate)

    result = await orchestrator.run_conversation(max_turns=8)

    return result


if __name__ == "__main__":
    asyncio.run(main())
