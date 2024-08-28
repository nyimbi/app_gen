CREATE TABLE "industry" (
  "id" SERIAL PRIMARY KEY,
  "industry_code" TEXT NOT NULL
);

CREATE TABLE "job" (
  "id" SERIAL PRIMARY KEY,
  "company_profile" TEXT NOT NULL,
  "about_job" TEXT NOT NULL,
  "responsibilities" TEXT NOT NULL,
  "salary" TEXT NOT NULL,
  "equity" TEXT NOT NULL,
  "offers_healthcare" BOOLEAN,
  "offers_vision" BOOLEAN,
  "offers_401k" BOOLEAN,
  "offers_dental" BOOLEAN,
  "paid_time_off" INTEGER,
  "vacation_days" INTEGER,
  "location" TEXT NOT NULL,
  "is_remote" BOOLEAN,
  "applicant_count" INTEGER,
  "job_filled" BOOLEAN
);

CREATE TABLE "industry_job" (
  "industry" INTEGER NOT NULL,
  "job" INTEGER NOT NULL,
  PRIMARY KEY ("industry", "job")
);

CREATE INDEX "idx_industry_job" ON "industry_job" ("job");

ALTER TABLE "industry_job" ADD CONSTRAINT "fk_industry_job__industry" FOREIGN KEY ("industry") REFERENCES "industry" ("id");

ALTER TABLE "industry_job" ADD CONSTRAINT "fk_industry_job__job" FOREIGN KEY ("job") REFERENCES "job" ("id");

CREATE TABLE "profilesource" (
  "id" SERIAL PRIMARY KEY,
  "import_script" TEXT NOT NULL
);

CREATE TABLE "skill" (
  "id" SERIAL PRIMARY KEY,
  "skill_value" INTEGER
);

CREATE TABLE "job_skill" (
  "skills" INTEGER NOT NULL,
  "jobs" INTEGER NOT NULL,
  PRIMARY KEY ("skills", "jobs")
);

CREATE INDEX "idx_job_skill__jobs" ON "job_skill" ("jobs");

ALTER TABLE "job_skill" ADD CONSTRAINT "fk_job_skill__jobs" FOREIGN KEY ("jobs") REFERENCES "job" ("id") ON DELETE CASCADE;

ALTER TABLE "job_skill" ADD CONSTRAINT "fk_job_skill__skills" FOREIGN KEY ("skills") REFERENCES "skill" ("id") ON DELETE CASCADE;

CREATE TABLE "userx" (
  "id" SERIAL PRIMARY KEY
);

CREATE TABLE "individual" (
  "id" SERIAL PRIMARY KEY,
  "userx" INTEGER NOT NULL,
  "is_individual" BOOLEAN,
  "is_institution" BOOLEAN,
  "is_company" BOOLEAN,
  "is_government" BOOLEAN,
  "is_online" BOOLEAN
);

CREATE INDEX "idx_individual__userx" ON "individual" ("userx");

ALTER TABLE "individual" ADD CONSTRAINT "fk_individual__userx" FOREIGN KEY ("userx") REFERENCES "userx" ("id");

CREATE TABLE "education" (
  "id" SERIAL PRIMARY KEY,
  "individual" INTEGER NOT NULL,
  "qualification" TEXT NOT NULL,
  "qual_class" TEXT NOT NULL,
  "verified" BOOLEAN,
  "verification_code" TEXT NOT NULL,
  "verified_by" TEXT NOT NULL,
  "verification_date" TIMESTAMP,
  "verification_doc" TEXT NOT NULL
);

CREATE INDEX "idx_education__individual" ON "education" ("individual");

ALTER TABLE "education" ADD CONSTRAINT "fk_education__individual" FOREIGN KEY ("individual") REFERENCES "individual" ("id") ON DELETE CASCADE;

CREATE TABLE "individual_job" (
  "individual" INTEGER NOT NULL,
  "job" INTEGER NOT NULL,
  PRIMARY KEY ("individual", "job")
);

CREATE INDEX "idx_individual_job" ON "individual_job" ("job");

ALTER TABLE "individual_job" ADD CONSTRAINT "fk_individual_job__individual" FOREIGN KEY ("individual") REFERENCES "individual" ("id");

ALTER TABLE "individual_job" ADD CONSTRAINT "fk_individual_job__job" FOREIGN KEY ("job") REFERENCES "job" ("id");

CREATE TABLE "location" (
  "id" SERIAL PRIMARY KEY,
  "individual" INTEGER NOT NULL
);

CREATE INDEX "idx_location__individual" ON "location" ("individual");

ALTER TABLE "location" ADD CONSTRAINT "fk_location__individual" FOREIGN KEY ("individual") REFERENCES "individual" ("id") ON DELETE CASCADE;

CREATE TABLE "portal" (
  "id" SERIAL PRIMARY KEY,
  "portal_url" TEXT NOT NULL,
  "is_primary" TEXT NOT NULL,
  "portal_state" TEXT NOT NULL,
  "individual" INTEGER,
  "has_custom_domain" BOOLEAN,
  "domain" TEXT NOT NULL,
  "header_text" TEXT NOT NULL,
  "slug" TEXT NOT NULL,
  "automatic_fulfillment_digital_products" BOOLEAN,
  "default_digital_max_downloads" INTEGER,
  "default_digital_url_valid_days" INTEGER,
  "default_mail_sender_name" TEXT NOT NULL,
  "default_mail_sender_address" TEXT NOT NULL,
  "fulfillment_auto_approve" BOOLEAN,
  "fulfillment_allow_unpaid" BOOLEAN,
  "reserve_stock_duration_anonymous_user" INTEGER,
  "reserve_stock_duration_authenticated_user" INTEGER,
  "limit_quantity_per_checkout" INTEGER,
  "gift_card_expiry_type" TEXT NOT NULL,
  "gift_card_expiry_period_type" TEXT NOT NULL,
  "gift_card_expiry_period" INTEGER,
  "charge_taxes_on_shipping" BOOLEAN,
  "include_taxes_in_prices" BOOLEAN,
  "display_gross_prices" BOOLEAN,
  "language" TEXT NOT NULL
);

CREATE INDEX "idx_portal__individual" ON "portal" ("individual");

ALTER TABLE "portal" ADD CONSTRAINT "fk_portal__individual" FOREIGN KEY ("individual") REFERENCES "individual" ("id") ON DELETE SET NULL;

CREATE TABLE "page" (
  "id" SERIAL PRIMARY KEY,
  "portal" INTEGER NOT NULL,
  "header" TEXT NOT NULL,
  "slug" TEXT NOT NULL,
  "page_type" TEXT NOT NULL
);

CREATE INDEX "idx_page__portal" ON "page" ("portal");

ALTER TABLE "page" ADD CONSTRAINT "fk_page__portal" FOREIGN KEY ("portal") REFERENCES "portal" ("id") ON DELETE CASCADE;

CREATE TABLE "profile" (
  "id" SERIAL PRIMARY KEY,
  "individual" INTEGER NOT NULL,
  "import_address" TEXT NOT NULL,
  "profile_username" TEXT NOT NULL,
  "profile_password" TEXT NOT NULL,
  "has_been_imported" BOOLEAN,
  "import_data" JSONB NOT NULL,
  "import_date" TIMESTAMP,
  "profilesource" INTEGER
);

CREATE INDEX "idx_profile__individual" ON "profile" ("individual");

CREATE INDEX "idx_profile__profilesource" ON "profile" ("profilesource");

ALTER TABLE "profile" ADD CONSTRAINT "fk_profile__individual" FOREIGN KEY ("individual") REFERENCES "individual" ("id") ON DELETE CASCADE;

ALTER TABLE "profile" ADD CONSTRAINT "fk_profile__profilesource" FOREIGN KEY ("profilesource") REFERENCES "profilesource" ("id") ON DELETE SET NULL;

CREATE TABLE "resume" (
  "id" SERIAL PRIMARY KEY,
  "individual" INTEGER NOT NULL,
  "template" TEXT NOT NULL,
  "header" TEXT NOT NULL,
  "color" TEXT NOT NULL,
  "location" INTEGER NOT NULL,
  "summary_text" TEXT NOT NULL,
  "has_been_generated" BOOLEAN,
  "preferred" BOOLEAN
);

CREATE INDEX "idx_resume__individual" ON "resume" ("individual");

CREATE INDEX "idx_resume__location" ON "resume" ("location");

ALTER TABLE "resume" ADD CONSTRAINT "fk_resume__individual" FOREIGN KEY ("individual") REFERENCES "individual" ("id") ON DELETE CASCADE;

ALTER TABLE "resume" ADD CONSTRAINT "fk_resume__location" FOREIGN KEY ("location") REFERENCES "location" ("id");

CREATE TABLE "swarm" (
  "id" SERIAL PRIMARY KEY,
  "portal" INTEGER NOT NULL
);

CREATE INDEX "idx_swarm__portal" ON "swarm" ("portal");

ALTER TABLE "swarm" ADD CONSTRAINT "fk_swarm__portal" FOREIGN KEY ("portal") REFERENCES "portal" ("id");

CREATE TABLE "individual_swarm" (
  "individual" INTEGER NOT NULL,
  "swarm" INTEGER NOT NULL,
  PRIMARY KEY ("individual", "swarm")
);

CREATE INDEX "idx_individual_swarm" ON "individual_swarm" ("swarm");

ALTER TABLE "individual_swarm" ADD CONSTRAINT "fk_individual_swarm__individual" FOREIGN KEY ("individual") REFERENCES "individual" ("id");

ALTER TABLE "individual_swarm" ADD CONSTRAINT "fk_individual_swarm__swarm" FOREIGN KEY ("swarm") REFERENCES "swarm" ("id");

CREATE TABLE "user_skill" (
  "skills" INTEGER NOT NULL,
  "user_details" INTEGER NOT NULL,
  PRIMARY KEY ("skills", "user_details")
);

CREATE INDEX "idx_user_skill__user_details" ON "user_skill" ("user_details");

ALTER TABLE "user_skill" ADD CONSTRAINT "fk_user_skill__skills" FOREIGN KEY ("skills") REFERENCES "skill" ("id") ON DELETE CASCADE;

ALTER TABLE "user_skill" ADD CONSTRAINT "fk_user_skill__user_details" FOREIGN KEY ("user_details") REFERENCES "individual" ("id") ON DELETE CASCADE;

CREATE TABLE "work_history" (
  "id" SERIAL PRIMARY KEY,
  "individual" INTEGER NOT NULL,
  "resume" INTEGER
);

CREATE INDEX "idx_work_history__individual" ON "work_history" ("individual");

CREATE INDEX "idx_work_history__resume" ON "work_history" ("resume");

ALTER TABLE "work_history" ADD CONSTRAINT "fk_work_history__individual" FOREIGN KEY ("individual") REFERENCES "individual" ("id") ON DELETE CASCADE;

ALTER TABLE "work_history" ADD CONSTRAINT "fk_work_history__resume" FOREIGN KEY ("resume") REFERENCES "resume" ("id") ON DELETE SET NULL