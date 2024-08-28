class Userxgraphql(graphene.ObjectType):
    userx = graphene.List(UserxObject)

class Individualgraphql(graphene.ObjectType):
    individual = graphene.List(IndividualObject)

class Industrygraphql(graphene.ObjectType):
    industry = graphene.List(IndustryObject)

class Industryjobgraphql(graphene.ObjectType):
    industry_job = graphene.List(IndustryJobObject)

class Jobgraphql(graphene.ObjectType):
    job = graphene.List(JobObject)

class Jobskillgraphql(graphene.ObjectType):
    job_skill = graphene.List(JobSkillObject)

class Skillgraphql(graphene.ObjectType):
    skill = graphene.List(SkillObject)

class Educationgraphql(graphene.ObjectType):
    education = graphene.List(EducationObject)

class Individualjobgraphql(graphene.ObjectType):
    individual_job = graphene.List(IndividualJobObject)

class Profilesourcegraphql(graphene.ObjectType):
    profilesource = graphene.List(ProfilesourceObject)

class Locationgraphql(graphene.ObjectType):
    location = graphene.List(LocationObject)

class Portalgraphql(graphene.ObjectType):
    portal = graphene.List(PortalObject)

class Pagegraphql(graphene.ObjectType):
    page = graphene.List(PageObject)

class Profilegraphql(graphene.ObjectType):
    profile = graphene.List(ProfileObject)

class Resumegraphql(graphene.ObjectType):
    resume = graphene.List(ResumeObject)

class Swarmgraphql(graphene.ObjectType):
    swarm = graphene.List(SwarmObject)

class Individualswarmgraphql(graphene.ObjectType):
    individual_swarm = graphene.List(IndividualSwarmObject)

class Userskillgraphql(graphene.ObjectType):
    user_skill = graphene.List(UserSkillObject)

class Workhistorygraphql(graphene.ObjectType):
    work_history = graphene.List(WorkHistoryObject)

class Query(graphene.ObjectType):
    userx = graphene.List(userxObject)
    individual = graphene.List(individualObject)
    industry = graphene.List(industryObject)
    industry_job = graphene.List(industry_jobObject)
    job = graphene.List(jobObject)
    job_skill = graphene.List(job_skillObject)
    skill = graphene.List(skillObject)
    education = graphene.List(educationObject)
    individual_job = graphene.List(individual_jobObject)
    profilesource = graphene.List(profilesourceObject)
    location = graphene.List(locationObject)
    portal = graphene.List(portalObject)
    page = graphene.List(pageObject)
    profile = graphene.List(profileObject)
    resume = graphene.List(resumeObject)
    swarm = graphene.List(swarmObject)
    individual_swarm = graphene.List(individual_swarmObject)
    user_skill = graphene.List(user_skillObject)
    work_history = graphene.List(work_historyObject)

    def resolve_userx(self, info):
        return userx.query.all()

    def resolve_individual(self, info):
        return individual.query.all()

    def resolve_industry(self, info):
        return industry.query.all()

    def resolve_industry_job(self, info):
        return industry_job.query.all()

    def resolve_job(self, info):
        return job.query.all()

    def resolve_job_skill(self, info):
        return job_skill.query.all()

    def resolve_skill(self, info):
        return skill.query.all()

    def resolve_education(self, info):
        return education.query.all()

    def resolve_individual_job(self, info):
        return individual_job.query.all()

    def resolve_profilesource(self, info):
        return profilesource.query.all()

    def resolve_location(self, info):
        return location.query.all()

    def resolve_portal(self, info):
        return portal.query.all()

    def resolve_page(self, info):
        return page.query.all()

    def resolve_profile(self, info):
        return profile.query.all()

    def resolve_resume(self, info):
        return resume.query.all()

    def resolve_swarm(self, info):
        return swarm.query.all()

    def resolve_individual_swarm(self, info):
        return individual_swarm.query.all()

    def resolve_user_skill(self, info):
        return user_skill.query.all()

    def resolve_work_history(self, info):
        return work_history.query.all()
