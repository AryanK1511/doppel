from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field, HttpUrl, field_validator


class PersonalInfoUrl(BaseModel):
    name: str = Field(..., description="URL label (e.g., LinkedIn, GitHub)")
    url: HttpUrl = Field(..., description="URL")


class PersonalInfo(BaseModel):
    full_name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    address: Optional[str] = Field(None, description="Address")
    age: Optional[int] = Field(None, description="Age")
    urls: Optional[list[PersonalInfoUrl]] = Field(
        None, description="URLs (LinkedIn, GitHub, etc.)"
    )


class WorkExperience(BaseModel):
    job_title: str = Field(..., description="Job title")
    company_name: str = Field(..., description="Company name")
    employment_type: str = Field(
        ..., description="Employment type (Full-time, Contract, etc.)"
    )
    location: str = Field(..., description="Location")
    start_date: str = Field(..., description="Start date")
    end_date: Optional[str] = Field(None, description="End date")
    currently_working: bool = Field(False, description="Currently working")
    responsibilities: list[str] = Field(..., description="Responsibilities")


class Education(BaseModel):
    degree: str = Field(..., description="Degree")
    field_of_study: str = Field(..., description="Field of study")
    institution: str = Field(..., description="Institution name")
    location: str = Field(..., description="Location")
    graduation_date: Optional[str] = Field(None, description="Graduation date")
    start_date: Optional[str] = Field(None, description="Start date")
    gpa: Optional[str] = Field(None, description="GPA")
    relevant_coursework: Optional[list[str]] = Field(
        None, description="Relevant coursework"
    )


class ProjectUrl(BaseModel):
    name: str = Field(..., description="URL label")
    url: HttpUrl = Field(..., description="URL")


class Project(BaseModel):
    project_name: str = Field(..., description="Project name")
    urls: Optional[list[ProjectUrl]] = Field(None, description="Project URLs")
    description: str = Field(..., description="Project description")


class Certification(BaseModel):
    certification_name: str = Field(..., description="Certification name")
    issuing_organization: str = Field(..., description="Issuing organization")
    date: str = Field(..., description="Certification date")


class AwardAchievement(BaseModel):
    title: str = Field(..., description="Award/achievement title")
    issuer: str = Field(..., description="Issuer")
    date: str = Field(..., description="Date")
    description: Optional[str] = Field(None, description="Description")


class CareerGoals(BaseModel):
    short_term: Optional[list[str]] = Field(None, description="Short-term goals")
    long_term: Optional[list[str]] = Field(None, description="Long-term goals")


class Availability(BaseModel):
    employment_status: str = Field(..., description="Employment status")
    available_to_start: str = Field(..., description="Available to start")
    open_to_opportunities: bool = Field(..., description="Open to opportunities")
    preferred_employment_type: list[str] = Field(
        ..., description="Preferred employment types"
    )


class RecruiterProfile(BaseModel):
    name: str = Field(..., description="Recruiter name")
    bio: str = Field(..., description="Recruiter bio")
    role_description: str = Field(
        ..., description="Role description for the position being filled"
    )
    candidate_selection_criteria: list[str] = Field(
        ..., min_length=1, description="Candidate selection criteria"
    )
    deal_breakers: Optional[list[str]] = Field(None, description="Deal breakers")
    positive_signals: Optional[list[str]] = Field(None, description="Positive signals")
    company_context: Optional[str] = Field(None, description="Company context")
    team_context: Optional[str] = Field(None, description="Team context")

    @field_validator("candidate_selection_criteria")
    @classmethod
    def validate_criteria(cls, v: list[str]) -> list[str]:
        if not v or len(v) == 0:
            raise ValueError("candidate_selection_criteria must have at least one item")
        return v


class CandidateProfile(BaseModel):
    personal_info: PersonalInfo = Field(..., description="Personal information")
    professional_summary: str = Field(..., description="Professional summary")
    work_experience: list[WorkExperience] = Field(
        ..., min_length=1, description="Work experience"
    )
    technical_skills: list[str] = Field(
        ..., min_length=1, description="Technical skills"
    )
    education: Optional[list[Education]] = Field(None, description="Education")
    projects: Optional[list[Project]] = Field(None, description="Projects")
    certifications: Optional[list[Certification]] = Field(
        None, description="Certifications"
    )
    awards_achievements: Optional[list[AwardAchievement]] = Field(
        None, description="Awards and achievements"
    )
    soft_skills: Optional[list[str]] = Field(None, description="Soft skills")
    languages: Optional[list[str]] = Field(None, description="Languages")
    professional_interests: Optional[list[str]] = Field(
        None, description="Professional interests"
    )
    hobbies: Optional[list[str]] = Field(None, description="Hobbies")
    career_goals: Optional[CareerGoals] = Field(None, description="Career goals")
    work_preferences: Optional[list[str]] = Field(None, description="Work preferences")
    availability: Optional[Availability] = Field(None, description="Availability")
    extra_curriculars: Optional[list[str]] = Field(
        None, description="Extra curriculars"
    )
    additional_context: Optional[str] = Field(None, description="Additional context")

    @field_validator("work_experience")
    @classmethod
    def validate_work_experience(cls, v: list[WorkExperience]) -> list[WorkExperience]:
        if not v or len(v) == 0:
            raise ValueError("work_experience must have at least one entry")
        return v

    @field_validator("technical_skills")
    @classmethod
    def validate_technical_skills(cls, v: list[str]) -> list[str]:
        if not v or len(v) == 0:
            raise ValueError("technical_skills must have at least one skill")
        return v


class CreateRecruiterAgentRequest(BaseModel):
    username: str = Field(..., description="Agent username")
    profile: RecruiterProfile = Field(..., description="Recruiter profile")


class CreateCandidateAgentRequest(BaseModel):
    username: str = Field(..., description="Agent username")
    profile: CandidateProfile = Field(..., description="Candidate profile")


class CreateAgentRequest(BaseModel):
    username: str = Field(..., description="Agent username")
    type: Literal["candidate", "recruiter"] = Field(..., description="Agent type")
    profile: dict = Field(
        ..., description="Profile data (RecruiterProfile or CandidateProfile)"
    )


class UpdateRecruiterProfile(BaseModel):
    name: Optional[str] = Field(None, description="Recruiter name")
    bio: Optional[str] = Field(None, description="Recruiter bio")
    role_description: Optional[str] = Field(None, description="Role description")
    candidate_selection_criteria: Optional[list[str]] = Field(
        None, description="Candidate selection criteria"
    )
    deal_breakers: Optional[list[str]] = Field(None, description="Deal breakers")
    positive_signals: Optional[list[str]] = Field(None, description="Positive signals")
    company_context: Optional[str] = Field(None, description="Company context")
    team_context: Optional[str] = Field(None, description="Team context")


class UpdateCandidateProfile(BaseModel):
    personal_info: Optional[PersonalInfo] = Field(
        None, description="Personal information"
    )
    professional_summary: Optional[str] = Field(
        None, description="Professional summary"
    )
    work_experience: Optional[list[WorkExperience]] = Field(
        None, description="Work experience"
    )
    technical_skills: Optional[list[str]] = Field(None, description="Technical skills")
    education: Optional[list[Education]] = Field(None, description="Education")
    projects: Optional[list[Project]] = Field(None, description="Projects")
    certifications: Optional[list[Certification]] = Field(
        None, description="Certifications"
    )
    awards_achievements: Optional[list[AwardAchievement]] = Field(
        None, description="Awards and achievements"
    )
    soft_skills: Optional[list[str]] = Field(None, description="Soft skills")
    languages: Optional[list[str]] = Field(None, description="Languages")
    professional_interests: Optional[list[str]] = Field(
        None, description="Professional interests"
    )
    hobbies: Optional[list[str]] = Field(None, description="Hobbies")
    career_goals: Optional[CareerGoals] = Field(None, description="Career goals")
    work_preferences: Optional[list[str]] = Field(None, description="Work preferences")
    availability: Optional[Availability] = Field(None, description="Availability")
    extra_curriculars: Optional[list[str]] = Field(
        None, description="Extra curriculars"
    )
    additional_context: Optional[str] = Field(None, description="Additional context")


class UpdateAgentRequest(BaseModel):
    username: Optional[str] = Field(None, description="Agent username")
    type: Optional[Literal["candidate", "recruiter"]] = Field(
        None, description="Agent type"
    )
    profile: Optional[dict] = Field(
        None, description="Profile data (RecruiterProfile or CandidateProfile)"
    )


class AgentListItem(BaseModel):
    agent_id: str = Field(..., description="Agent document ID")
    username: str = Field(..., description="Agent username")
    name: str = Field(..., description="Agent name")
    bio: str = Field(..., description="Agent bio")
    type: str = Field(..., description="Agent type")
    created_at: str = Field(..., description="ISO format timestamp of creation")


class AgentResponse(BaseModel):
    agent_id: str = Field(..., description="Agent document ID")
    username: str = Field(..., description="Agent username")
    name: str = Field(..., description="Agent name")
    bio: str = Field(..., description="Agent bio")
    type: str = Field(..., description="Agent type")
    profile: dict = Field(..., description="Profile data")
    created_at: str = Field(..., description="ISO format timestamp of creation")
