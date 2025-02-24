CREATE TYPE "t_verification_status" AS ENUM (
  'pending',
  'kyc_submitted',
  'kyc_approved',
  'kyc_rejected',
  'escalated',
  'contracted',
  'active',
  'suspended',
  'inactive',
  'contract_terminated',
  'docs_expired',
  'under_review',
  'locked',
  'awaiting_renewal',
  'renewal_rejected',
  'verification_failed'
);

CREATE TYPE "t_org_type" AS ENUM (
  'Individual',
  'Business_Name',
  'Sole_Proprietorship',
  'Private_Limited_Company',
  'Public_Limited_Company',
  'Public_Company_Limited_by_Guarantee',
  'Private_Unlimited_Company',
  'Public_Unlimited_Company'
);

CREATE TYPE "t_person_role" AS ENUM (
  'next_of_kin',
  'company_director',
  'pos_operator',
  'field_support',
  'customer',
  'referee',
  'supervisor',
  'agent'
);

CREATE TYPE "t_agent_role" AS ENUM (
  'agent',
  'sub_agent',
  'super_agent',
  'aggregator',
  'operator'
);

CREATE TYPE "t_gender" AS ENUM (
  'Male',
  'Female',
  'Non_Binary',
  'Prefer_Not_to_Say',
  'Other'
);

CREATE TYPE "t_card_trans_type" AS ENUM (
  'purchase',
  'balance',
  'refund',
  'cash_advance',
  'cash_back',
  'pre_authorization',
  'pre_authorization_completion',
  'card_verification',
  'transaction',
  'settlement',
  'settlement_batch_upload',
  'withdrawal',
  'deposit',
  'transfer',
  'bill_payment',
  'cash_deposit',
  'card_activation'
);

CREATE TYPE "t_severity_level" AS ENUM (
  'Insignificant',
  'Trivial',
  'Low',
  'Moderate',
  'Significant',
  'High',
  'Urgent',
  'Severe',
  'Extreme',
  'Critical'
);

CREATE TYPE "t_payment_method" AS ENUM (
  'cash',
  'credit_card',
  'debit_card',
  'prepaid_card',
  'commercial_card',
  'debt',
  'bank',
  'mobile',
  'coupon',
  'order',
  'withdrawal',
  'fund_wallet',
  'cheque',
  'bank_transfer',
  'crypto',
  'barter',
  'wire_transfer',
  'contactless',
  'gift_card',
  'loyalty_points',
  'money_order',
  'escrow',
  'installment',
  'invoice',
  'prepaid',
  'qr_code',
  'digital_wallet',
  'automatic_debit',
  'cash_on_delivery',
  'postpaid',
  'third_party',
  'trade_credit'
);

CREATE TYPE "t_transaction_status" AS ENUM (
  'pending',
  'authorized',
  'completed',
  'failed',
  'cancelled',
  'refunded',
  'reversed',
  'hold',
  'suspended',
  'disputed',
  'delivered',
  'settlement_pending',
  'settled',
  'rejected',
  'expired',
  'pending_verification',
  'hold_for_review',
  'partially_completed',
  'partially_refunded',
  'partially_reversed',
  'completed_with_errors',
  'batch_processing',
  'deferred',
  'waiting_for_authorization',
  'processing',
  'pending_funds_availability',
  'pending_review',
  'pending_confirmation',
  'waiting_for_settlement',
  'pending_reconciliation',
  'pending_disbursement',
  'chargeback_initiated',
  'chargeback_resolved',
  'pending_capture',
  'captured',
  'voided',
  'in_queue',
  'manual_intervention_required',
  'gateway_timeout',
  'fraud_alert',
  'under_audit',
  'audit_completed',
  'currency_conversion',
  'currency_conversion_completed',
  'escalated',
  'de_escalated',
  'pending_approval',
  'approved',
  'declined',
  're_attempted',
  're_scheduled',
  'insufficient_funds',
  'verification_failed',
  'verification_successful',
  'pending_clearance',
  'cleared',
  're_initiated',
  'split_transaction',
  'consolidated'
);

CREATE TYPE "t_doc_category" AS ENUM (
  'Identification',
  'Certification',
  'Financial',
  'Educational',
  'Legal_Document',
  'Utility_Bill',
  'Medical_Report',
  'Contract',
  'Insurance_Policy',
  'Tax_Document',
  'Proof_of_Address'
);

CREATE TYPE "t_doc_status" AS ENUM (
  'not_started',
  'draft',
  'in_progress',
  'awaiting_review',
  'under_review',
  'review_completed',
  'revisions_needed',
  'submitted',
  'approved',
  'partially_approved',
  'rejected',
  'cancelled',
  'archived',
  'published',
  'suspended',
  'voided',
  'completed',
  'expired',
  'renewed',
  'locked',
  'merged',
  'rollback',
  'conflict',
  'queued_for_review',
  'queued_for_publish',
  'deprecated',
  'unpublished',
  'in_translation',
  'validation_failed',
  'validation_passed',
  'digitized',
  'in_signature_process',
  'signature_completed',
  'signature_failed',
  'in_audit',
  'audit_completed',
  'in_transit',
  'received',
  'sent',
  'wip'
);

CREATE TYPE "t_interval" AS ENUM (
  'None',
  'Per_Second',
  'Per_Minute',
  'Hourly',
  'Daily',
  'Weekly',
  'Biweekly',
  'Monthly',
  'Bimonthly',
  'Quarterly',
  'Semi_Annually',
  'Annually',
  'Custom',
  'Workdays',
  'Weekends',
  'MONDAY',
  'TUESDAY',
  'WEDNESDAY',
  'THURSDAY',
  'FRIDAY',
  'SATURDAY',
  'SUNDAY',
  'FIRST_DAY_MONTH',
  'LAST_DAY_MONTH',
  'FIRST_WEEKDAY',
  'LAST_WEEKDAY',
  'EVERY_X_DAYS',
  'EVERY_X_WEEKS',
  'EVERY_X_MONTHS',
  'EVERY_X_YEARS'
);

CREATE TYPE "t_date_macro" AS ENUM (
  'All',
  'Today',
  'ThisWeek',
  'ThisWeekToDate',
  'ThisMonth',
  'ThisMonthToDate',
  'ThisCalendarQuarter',
  'ThisCalendarQuarterToDate',
  'ThisFiscalQuarter',
  'ThisFiscalQuarterToDate',
  'ThisCalendarYear',
  'ThisCalendarYearToDate',
  'ThisFiscalYear',
  'ThisFiscalYearToDate',
  'Yesterday',
  'LastWeek',
  'LastWeekToDate',
  'LastMonth',
  'LastMonthToDate',
  'LastCalendarQuarter',
  'LastCalendarQuarterToDate',
  'LastFiscalQuarter',
  'LastFiscalQuarterToDate',
  'LastCalendarYear',
  'LastCalendarYearToDate',
  'LastFiscalYear',
  'LastFiscalYearToDate',
  'NextWeek',
  'NextFourWeeks',
  'NextMonth',
  'NextCalendarQuarter',
  'NextCalendarYear',
  'NextFiscalQuarter',
  'NextFiscalYear'
);

CREATE TABLE "country" (
  "id" INT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  "name" varchar(100),
  "code" varchar(5) UNIQUE,
  "phone_code" varchar(15)
);

CREATE TABLE "state" (
  "country_id_fk" int,
  "id" INT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  "code" varchar(5) UNIQUE,
  "name" varchar(50),
  "description" text
);

CREATE TABLE "lga" (
  "id" INT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  "state_id_fk" int,
  "code" varchar(50),
  "lga_name" varchar(100)
);

CREATE TABLE "ward" (
  "id" INT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  "lga_id_fk" int,
  "ward_name" varchar(100)
);

CREATE TABLE "techparam" (
  "id" serial PRIMARY KEY,
  "tp_key" varchar(50),
  "tp_value" text,
  "enabled" boolean DEFAULT true,
  "notes" text
);

CREATE TABLE "mime_type" (
  "id" serial PRIMARY KEY,
  "label" varchar(200),
  "mime_type" varchar(150) UNIQUE,
  "file_extension" varchar(10)
);

CREATE TABLE "mime_type_map" (
  "id" serial PRIMARY KEY,
  "extension" varchar(10),
  "mime_type" varchar(150)
);

CREATE TABLE "bank" (
  "id" INT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  "code" varchar(50) NOT NULL,
  "name" varchar(255) NOT NULL,
  "category" int DEFAULT 2,
  "swift_code" varchar(50) UNIQUE,
  "sort_code" varchar(50) UNIQUE,
  "iban" varchar(50) UNIQUE,
  "cust_care_phone" varchar(30),
  "cust_care_email" varchar(50),
  "escalation_contact" text
);

CREATE TABLE "doc_type" (
  "id" serial PRIMARY KEY,
  "name" varchar(200),
  "doc_category" t_doc_category,
  "notes" text,
  "required_information" text,
  "is_serialized" boolean DEFAULT false,
  "serial_length" int,
  "expires" boolean DEFAULT false,
  "validity_period" int,
  "renewal_frequency" int,
  "is_government_issued" boolean DEFAULT false,
  "is_digital" boolean DEFAULT false,
  "template_url" varchar(255),
  "example_image_url" varchar(255),
  "created_at" timestamp DEFAULT (now()),
  "updated_at" timestamp DEFAULT (now())
);

CREATE TABLE "agent_tier" (
  "id" INT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  "name" varchar(100),
  "notes" text
);

CREATE TABLE "user_ext" (
  "id" INT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  "manager_id_fk" int,
  "full_name" varchar(50),
  "employee_number" varchar(50),
  "job_title" varchar(50),
  "phone_number" varchar(50),
  "email" varchar(50),
  "user_data" text
);

CREATE TABLE "agent" (
  "id" serial PRIMARY KEY,
  "aggregator_id_fk" int,
  "is_aggregator" boolean DEFAULT false,
  "became_aggregator_date" timestamp,
  "assigned_pos_count" int NOT NULL DEFAULT 0,
  "aggregator_pos_threshold" int DEFAULT 20,
  "verification_status" t_verification_status,
  "verification_status_notes" text,
  "agent_type" t_org_type DEFAULT 'Individual',
  "agent_role" t_agent_role,
  "agent_tier_id_fk" int,
  "account_manager_id_fk" int,
  "name" varchar(255),
  "alias" varchar(150),
  "phone_country_id_fk" int,
  "phone" varchar(20) NOT NULL,
  "phone_ext" varchar(10),
  "alt_phone_country_id_fk" int,
  "alt_phone" varchar(20),
  "alt_phone_ext" varchar(10),
  "email" varchar(255) UNIQUE,
  "alt_email" varchar(255) UNIQUE,
  "bvn" varchar(50),
  "bvn_verified" boolean DEFAULT false,
  "bvn_verification_date" timestamp DEFAULT (now()),
  "bvn_verification_code" text,
  "tax_id" varchar(50),
  "bank_id_fk" int,
  "bank_acc_no" varchar(30),
  "biz_name" varchar(255),
  "biz_state_id_fk" int,
  "biz_lga_id_fk" int,
  "biz_city" varchar(50),
  "biz_city_area" varchar(100),
  "biz_street" varchar(100),
  "biz_building" varchar(100),
  "biz_address" text,
  "biz_poa_img" varchar(255),
  "biz_poa_desc" varchar(255),
  "biz_poa_valid" boolean DEFAULT false,
  "biz_lat" float,
  "biz_lon" float,
  "biz_loc" text,
  "biz_ggl_code" varchar,
  "company_name" varchar,
  "cac_number" varchar,
  "cac_reg_date" date,
  "cac_cert_img" varchar,
  "cac_cert_no" varchar,
  "ref_code" varchar(255),
  "access_pin" varchar(10),
  "registered_by_id_fk" int,
  "registration_date" timestamp DEFAULT (now()),
  "reviewed_by_id_fk" int,
  "review_date" timestamp DEFAULT (now()),
  "approved_by_id_fk" int,
  "approval_date" timestamp,
  "approval_narrative" text,
  "kyc_submit_date" timestamp,
  "kyc_verification_status" t_verification_status DEFAULT 'pending',
  "kyc_approval_date" timestamp,
  "kyc_ref_code" varchar(255),
  "kyc_rejection_narrative" text,
  "kyc_rejection_by_id_fk" int,
  "rejection_date" timestamp,
  "rejection_narrative" text,
  "rejected_by_id_fk" int,
  "face_matrix" text,
  "finger_print_img" text,
  "agent_public_key" text,
  "agent_pj_expiry" timestamp,
  "agent_history" text
);

CREATE TABLE "contact_type" (
  "id" serial PRIMARY KEY,
  "name" varchar(50) NOT NULL,
  "description" text,
  "is_digital" boolean DEFAULT true,
  "requires_verification" boolean DEFAULT false,
  "max_length" int,
  "icon_url" varchar(255),
  "created_at" timestamp DEFAULT 'now()',
  "updated_at" timestamp DEFAULT 'now()'
);

CREATE TABLE "contact" (
  "id" serial PRIMARY KEY,
  "person_id_fk" int,
  "agent_id_fk" int,
  "contact_type_id_fk" int NOT NULL,
  "contact" varchar(100) NOT NULL,
  "priority" int NOT NULL DEFAULT 10,
  "best_time_to_contact_start" time,
  "best_time_to_contact_end" time,
  "active_from_date" timestamp DEFAULT (now()),
  "active_to_date" date,
  "for_business_use" boolean DEFAULT false,
  "for_personal_use" boolean DEFAULT true,
  "do_not_use" boolean DEFAULT false,
  "is_active" boolean DEFAULT true,
  "is_blocked" boolean DEFAULT false,
  "is_verified" boolean DEFAULT false,
  "notes" text
);

CREATE TABLE "agent_person_link" (
  "person_id_fk" int NOT NULL,
  "agent_id_fk" int NOT NULL,
  PRIMARY KEY ("person_id_fk", "agent_id_fk")
);

CREATE TABLE "person" (
  "id" serial PRIMARY KEY,
  "agent_id_fk" int NOT NULL,
  "next_of_kin_id_fk" int,
  "person_role" t_person_role,
  "first_name" varchar(255),
  "middle_name" varchar(255),
  "surname" varchar(255),
  "nick_name" varchar(255),
  "gender" t_gender DEFAULT 'Male',
  "photo_img" varchar(255),
  "signature_img" varchar(255),
  "bvn_no" varchar(255),
  "bvn_verified" boolean DEFAULT false,
  "bvn_verification_date" timestamp DEFAULT (now()),
  "bvn_verification_code" text,
  "tax_id" varchar(255),
  "home_poa_img" varchar(255),
  "home_poa_desc" varchar(255),
  "home_poa_valid" boolean DEFAULT false,
  "home_lat" float,
  "home_lon" float,
  "home_loc" text,
  "home_ggl_code" varchar
);

CREATE TABLE "person_admin_data" (
  "person_id_fk" int PRIMARY KEY NOT NULL,
  "creation_time" timestamp DEFAULT (now()),
  "failed_login_count" int DEFAULT 0,
  "failed_login_timestamp" timestamp,
  "password_last_set_time" timestamp,
  "profile_picture" varchar(500),
  "awatar" varchar(500),
  "screen_name" varchar(60),
  "user_priv_cert" text,
  "user_pub_cert" text,
  "alt_security_identities" text,
  "generated_UID" UUID,
  "do_not_email" boolean DEFAULT false,
  "do_not_phone" boolean DEFAULT false,
  "do_not_mail" boolean DEFAULT false,
  "do_not_sms" boolean DEFAULT false,
  "do_not_trade" boolean DEFAULT false,
  "opted_out" boolean DEFAULT false,
  "do_not_track_update_date" date,
  "do_not_process_from_update_date" date,
  "do_not_market_from_update_date" date,
  "do_not_track_location_update_date" date,
  "do_not_profile_from_update_date" date,
  "do_forget_me_from_update_date" date,
  "do_not_process_reason" varchar(500),
  "no_merge_reason" varchar(500),
  "do_extract_my_data_update_date" date,
  "should_forget" boolean,
  "consumer_credit_score_provider_name" varchar(500),
  "web_site_url" varchar(500),
  "ordering_name" varchar(500),
  "hospitalizations_last5_years_count" integer,
  "surgeries_last5_years_count" integer,
  "dependent_count" integer,
  "account_locked" boolean DEFAULT false,
  "send_individual_data" boolean,
  "influencer_rating" integer
);

CREATE TABLE "agent_doc_link" (
  "agent_id_fk" int NOT NULL,
  "doc_id_fk" int NOT NULL,
  "verification_status" t_verification_status DEFAULT 'pending',
  "submit_date" timestamp DEFAULT (now()),
  "notes" text,
  PRIMARY KEY ("agent_id_fk", "doc_id_fk")
);

CREATE TABLE "person_doc_link" (
  "person_id_fk" int NOT NULL,
  "doc_id_fk" int NOT NULL,
  "verification_status" t_verification_status DEFAULT 'pending',
  "submit_date" timestamp DEFAULT (now()),
  PRIMARY KEY ("person_id_fk", "doc_id_fk")
);

CREATE TABLE "doc" (
  "id" serial PRIMARY KEY,
  "doc_type_id_fk" int,
  "person_id_fk" int,
  "agent_id_fk" int,
  "doc_front_img" text,
  "doc_back_img" text,
  "doc_name" varchar(100),
  "doc_content_type_id_fk" int,
  "doc_url" text,
  "doc_length" int,
  "doc_text" text,
  "identification_number" varchar(100),
  "serial_number" varchar(100),
  "description" text,
  "file_name" varchar(500),
  "page_count" int,
  "issued_on" date,
  "issued_by_authority" varchar(500),
  "issued_at" varchar(500),
  "expires_on" date,
  "is_expired" boolean DEFAULT false,
  "verified" boolean DEFAULT false,
  "verification_date" timestamp DEFAULT (now()),
  "verification_code" text,
  "uploaded_on" timestamp DEFAULT (now()),
  "updated_on" timestamp DEFAULT (now())
);

CREATE TABLE "pos" (
  "id" INT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  "serial_no" varchar(255) UNIQUE,
  "imei" varchar(255),
  "mac_addr" varchar(255),
  "device_model" varchar(255),
  "device_make" varchar(255),
  "device_mfg" varchar(255),
  "os_version" varchar(255),
  "device_color" varchar(50),
  "device_condition" varchar,
  "status" varchar(255),
  "owner_type" varchar(50),
  "registration_date" timestamp DEFAULT (now()),
  "assigned" boolean DEFAULT false,
  "assigned_date" timestamp,
  "assigned_narrative" text,
  "active" boolean DEFAULT false,
  "activation_date" timestamp DEFAULT (now()),
  "last_active" timestamp,
  "deployed" boolean DEFAULT false,
  "deploy_date" timestamp,
  "deploy_narrative" text,
  "returned" boolean DEFAULT false,
  "return_date" timestamp,
  "return_narrative" text,
  "return_received_date" timestamp,
  "return_received_by_id_fk" int,
  "state_id_fk" integer,
  "lga_id_fk" integer,
  "street_address" varchar(255),
  "building_name" varchar(255),
  "contact_phone_num" varchar(80),
  "pos_user" varchar(100),
  "crypt_priv_key" text,
  "crypt_pub_key" text,
  "crypt_password" text,
  "override_key" text
);

CREATE TABLE "agent_pos_link" (
  "agent_id_fk" int NOT NULL,
  "pos_id_fk" int NOT NULL,
  "assigned_date" timestamp DEFAULT (now()),
  "assigned_by" varchar,
  "received_by" varchar,
  "received_date" timestamp,
  "received_location" varchar,
  "delivery_note" text,
  "delivery_note_printed" boolean DEFAULT false,
  "activated" boolean DEFAULT false,
  "activation_date" timestamp,
  "activation_otp" varchar(20),
  "otp_sent" boolean DEFAULT false,
  "otp_sent_time" timestamp,
  "otp_used" boolean DEFAULT false,
  "history" text,
  PRIMARY KEY ("agent_id_fk", "pos_id_fk")
);

CREATE TABLE "token_provider" (
  "id" serial PRIMARY KEY,
  "name" varchar(200) NOT NULL,
  "notes" text,
  "priv_key" text,
  "pub_key" text,
  "endpoint" text,
  "protocol" text,
  "auth" text,
  "ssl" text,
  "ip_whitelist" text,
  "password" varchar(255),
  "enabled" boolean DEFAULT false
);

CREATE TABLE "token" (
  "id" INT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  "token_provider_id_fk" int,
  "token_name" varchar(200),
  "token_issue_date" timestamp DEFAULT (now()),
  "token_expiry_date" timestamp DEFAULT (now()),
  "token_validity" int,
  "token_expired" boolean DEFAULT false,
  "token_value" varchar(255),
  "token_username" varchar(255),
  "token_password" varchar(255),
  "token_notes" text,
  "token_client_secret" text,
  "enabled" boolean DEFAULT false
);

CREATE TABLE "biller_category" (
  "id" INT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  "name" varchar(250),
  "notes" text
);

CREATE TABLE "biller" (
  "id" INT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  "category_id_fk" int,
  "code" varchar(10) UNIQUE NOT NULL,
  "name" varchar(255),
  "url" varchar,
  "note" text
);

CREATE TABLE "biller_offering" (
  "biller_id_fk" int,
  "id" INT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  "name" varchar(255),
  "description" text,
  "price" Numeric(10,2)
);

CREATE TABLE "trans_type" (
  "id" INT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  "name" varchar(100),
  "notes" text
);

CREATE TABLE "customer_segment" (
  "id" INT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  "name" varchar(100),
  "notes" text
);

CREATE TABLE "risk_profile" (
  "id" int PRIMARY KEY,
  "name" varchar(100),
  "description" text,
  "risk_score" int,
  "risk_category" varchar(100),
  "max_acceptable_loss" decimal,
  "probability_of_loss" decimal,
  "historical_volatility" decimal,
  "liquidity_rating" int,
  "regulatory_compliance" varchar(100),
  "market_sensitivity" decimal,
  "credit_rating" varchar(50),
  "investment_horizon" varchar(100),
  "sector_exposure" varchar(100),
  "geographic_exposure" varchar(100)
);

CREATE TABLE "commission" (
  "id" INT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  "agent_type" t_org_type,
  "agent_tier_level_id_fk" int,
  "agent_id_fk" int,
  "state_id_fk" int,
  "lga_id_fk" int,
  "currency_id_fk" int,
  "risk_profile_id_fk" int,
  "biller_id_fk" int,
  "biller_offering_id_fk" int,
  "transaction_type_id_fk" int,
  "customer_segment_id_fk" int,
  "special_promotion_id_fk" int,
  "min_trans_amount" Numeric(10,2) DEFAULT 0,
  "max_trans_amount" Numeric(10,2),
  "min_max_step" integer,
  "min_comm_amount" Numeric(10,2) DEFAULT 0,
  "max_comm_amount" Numeric(10,2),
  "commission_rate" Numeric(10,5),
  "start_time" timestamp DEFAULT null,
  "end_time" timestamp DEFAULT null,
  "start_date" timestamp DEFAULT null,
  "end_date" timestamp DEFAULT null
);

CREATE TABLE "promotion" (
  "id" INT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  "name" varchar,
  "notes" text,
  "start_date" timestamp,
  "end_date" timestamp
);

CREATE TABLE "currency" (
  "id" SERIAL PRIMARY KEY,
  "name" varchar(4),
  "symbol" varchar(5),
  "numeric_code" varchar(4),
  "full_name" varchar(100),
  "decimal_places" SMALLINT,
  "internationalized_name_code" varchar(90)
);

CREATE TABLE "trans_routing_threshold" (
  "id" INT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  "name" varchar(255),
  "min_amount" Numeric(10,2),
  "max_amount" Numeric(10,2),
  "priority" int DEFAULT 10
);

CREATE TABLE "transaction" (
  "id" INT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  "coupon_id_fk" int,
  "customer_name" varchar,
  "trans_purpose" text,
  "customer_id" varchar,
  "transaction_type" t_payment_method DEFAULT 'withdrawal',
  "card_trans_type" t_card_trans_type DEFAULT 'purchase',
  "agent_id_fk" int NOT NULL,
  "payment_card_id_fk" int,
  "pos_id_fk" int,
  "wallet_id_fk" int,
  "biller_id_fk" int,
  "biller_offering_id_fk" int,
  "trans_time" timestamp DEFAULT (now()),
  "currency_id_fk" int,
  "trans_status" t_transaction_status,
  "trans_route_id_fk" int,
  "origin_source" t_payment_method,
  "origin_ref_code" varchar(200),
  "origin_trans_notes" text,
  "origin_bank_id_fk" int,
  "origin_institution_code" varchar(200),
  "origin_account_num" varchar(50),
  "origin_account_name" varchar(200),
  "origin_KYC_Level" int,
  "origin_Bank_Verification_Number" varchar(200),
  "origin_bvn" varchar(200),
  "session_ref" varchar(200),
  "transaction_ref" varchar(200),
  "channelCode" int,
  "name_enquiry_ref" varchar(200),
  "api_transactionid" varchar(100),
  "receipt_no" varchar(100),
  "pin_based" boolean DEFAULT false,
  "pin_code" varchar(100),
  "pin_option" varchar(100),
  "authorization_code" varchar(200),
  "acquirer_name" varchar(30),
  "currency" varchar(30),
  "transaction_location" varchar(200),
  "payment_reference" varchar(200),
  "response_code" varchar(30),
  "trans_dest" t_payment_method,
  "bene_ref_code" varchar(200),
  "bene_trans_notes" text,
  "bene_bank_id_fk" int,
  "bene_account_num" varchar(50),
  "bene_institution_code" varchar(200),
  "bene_bank_verification_number" varchar(200),
  "bene_KYC_Level" int,
  "bene_account_name" varchar(200),
  "bene_phone_number" varchar(30),
  "bene_phone_denom" varchar(10),
  "bene_phone_product" varchar(100),
  "transaction_amount" Numeric(10,2),
  "available_balance" Numeric(10,2),
  "svc_fees" Numeric(10,2) DEFAULT 0,
  "comm_total" Numeric(10,2),
  "comm_agent" Numeric(10,2),
  "comm_aggr" Numeric(10,2),
  "comm_ours" Numeric(10,2),
  "comm_other" Numeric(10,2) DEFAULT 0,
  "comm_net_pct" float,
  "tax" Numeric(10,2),
  "excise_duty" Numeric(10,2),
  "vat" Numeric(10,2),
  "transmit_amount" Numeric(10,2),
  "comm_narration" text,
  "trans_currency" varchar(3) DEFAULT 'NGN',
  "trans_convert_currency" varchar(3),
  "trans_currency_exchange_rate" Numeric(10,2) DEFAULT 1,
  "trans_date" timestamp DEFAULT (now()),
  "customer_segment_id_fk" int,
  "agent_tier_level_id_fk" int,
  "special_promotions_id_fk" int,
  "risk_profile_id_fk" int,
  "fraud_marker" boolean DEFAULT false,
  "fraud_eval_outcome" varchar(20),
  "fraud_risk_score" float DEFAULT 0,
  "fraud_prediction_explanations" text,
  "fraud_rule_evaluations" text,
  "fraud_event_num" varchar(250),
  "trans_narration" text
);

CREATE TABLE "payment_card" (
  "id" SERIAL PRIMARY KEY,
  "bin" varchar(20),
  "pan" varchar(20),
  "credit_card_expired" boolean NOT NULL DEFAULT false,
  "card_token" varchar(500) NOT NULL,
  "issue_number" varchar(500) NOT NULL,
  "bill_to_city" varchar(500),
  "masked_number" varchar(500) NOT NULL,
  "name" varchar(500) NOT NULL,
  "company_name" varchar(500),
  "card_holder_name" varchar(500) NOT NULL,
  "number_last_digits" varchar(500) NOT NULL,
  "payment_card_type" varchar(500) NOT NULL,
  "derived_card_type_code" varchar(500),
  "expiration_year" int,
  "expiration_month" int,
  "bill_to_street" varchar(500),
  "bill_to_street2" varchar(500),
  "bill_to_first_name" varchar(500),
  "bill_to_last_name" varchar(20),
  "payment_method_status" varchar(500),
  "card_number" varchar(60),
  "cardholder_name" varchar(30),
  "card_expiration" varchar(30),
  "service_code" varchar(30),
  "cvv" varchar(30)
);

CREATE TABLE "coupon" (
  "id" INT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  "value" Numeric(10,2),
  "serial_no" varchar(100),
  "active" boolean,
  "used" boolean DEFAULT false,
  "used_date" timestamp,
  "primary_scan_code_label" varchar(500),
  "is_return_coupon" boolean,
  "expiration_date" date,
  "generation_date" timestamp DEFAULT (now()),
  "activation_date" timestamp DEFAULT (now()),
  "secondary_scan_code_label" varchar(500),
  "scan_code_img" varchar(500),
  "coupon_code" varchar(500),
  "return_coupon_reason" varchar(500),
  "is_valid" boolean DEFAULT true,
  "coupon_status" varchar(50),
  "discount_percentage" integer,
  "coupon_count" integer,
  "payment_method_status" varchar(500) NOT NULL
);

CREATE TABLE "wallet" (
  "id" INT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  "agent_id_fk" int,
  "pos_id_fk" int,
  "wallet_name" varchar(255),
  "wallet_balance" numeric(10,3),
  "wallet_locked" boolean DEFAULT false,
  "wallet_active" boolean DEFAULT true,
  "wallet_code" varchar(50),
  "wallet_crypt" text,
  "wallet_narrative" text
);

CREATE INDEX ON "techparam" ("tp_key");

CREATE INDEX ON "mime_type" ("label");

CREATE INDEX ON "mime_type" ("mime_type");

CREATE INDEX ON "mime_type" ("file_extension");

CREATE INDEX ON "mime_type_map" ("extension");

CREATE INDEX ON "mime_type_map" ("extension", "mime_type");

CREATE UNIQUE INDEX ON "doc_type" ("name");

CREATE UNIQUE INDEX "idx_unique_name" ON "contact_type" ("name");

CREATE UNIQUE INDEX "idx_person_contact" ON "contact" ("person_id_fk", "contact_type_id_fk");

CREATE UNIQUE INDEX "idx_org_contact" ON "contact" ("agent_id_fk", "contact_type_id_fk");

CREATE UNIQUE INDEX "idx_unique_contact" ON "contact" ("contact");

CREATE INDEX ON "agent_person_link" ("person_id_fk");

CREATE INDEX ON "agent_person_link" ("agent_id_fk");

CREATE INDEX ON "person" ("agent_id_fk");

CREATE INDEX ON "person" ("first_name", "middle_name", "surname");

CREATE INDEX ON "person_admin_data" ("person_id_fk");

CREATE INDEX ON "agent_doc_link" ("agent_id_fk");

CREATE INDEX ON "agent_doc_link" ("doc_id_fk");

CREATE INDEX ON "person_doc_link" ("person_id_fk");

CREATE INDEX ON "person_doc_link" ("doc_id_fk");

CREATE INDEX ON "doc" ("doc_name");

CREATE INDEX ON "doc" ("doc_type_id_fk");

CREATE INDEX ON "doc" ("issued_on");

CREATE INDEX ON "doc" ("verified");

CREATE UNIQUE INDEX ON "currency" ("name");

CREATE UNIQUE INDEX ON "trans_routing_threshold" ("id");

CREATE INDEX ON "transaction" ("customer_name");

CREATE INDEX ON "transaction" ("customer_id");

CREATE INDEX ON "transaction" ("session_ref");

CREATE INDEX ON "transaction" ("transaction_ref");

CREATE INDEX ON "transaction" ("risk_profile_id_fk");

COMMENT ON TABLE "country" IS 'List of Countries';

COMMENT ON COLUMN "country"."name" IS 'Country Name';

COMMENT ON COLUMN "country"."code" IS 'Country Code';

COMMENT ON COLUMN "country"."phone_code" IS 'Dialling prefix of the country e.g +234 for Nigeria';

COMMENT ON TABLE "state" IS 'List of States';

COMMENT ON COLUMN "state"."id" IS 'ID of this column';

COMMENT ON COLUMN "state"."code" IS 'State Code';

COMMENT ON COLUMN "state"."name" IS 'Name of the state';

COMMENT ON COLUMN "state"."description" IS 'Brief description of the state';

COMMENT ON TABLE "lga" IS 'Local Government Area';

COMMENT ON COLUMN "lga"."id" IS 'ID of this column';

COMMENT ON COLUMN "lga"."state_id_fk" IS 'Foreign Key of the state';

COMMENT ON COLUMN "lga"."code" IS 'Local Government Code';

COMMENT ON COLUMN "lga"."lga_name" IS 'LGA Name';

COMMENT ON TABLE "ward" IS 'Ward';

COMMENT ON COLUMN "ward"."id" IS 'ID of this column';

COMMENT ON COLUMN "ward"."lga_id_fk" IS 'Parent LGA';

COMMENT ON COLUMN "ward"."ward_name" IS 'Ward Name';

COMMENT ON COLUMN "techparam"."tp_key" IS 'Tech Param Key';

COMMENT ON COLUMN "techparam"."tp_value" IS 'Tech Param Value';

COMMENT ON COLUMN "techparam"."enabled" IS 'Is this param used';

COMMENT ON COLUMN "techparam"."notes" IS 'Notes on this parameter';

COMMENT ON TABLE "mime_type" IS 'Standard MIME types recognized by the content management system.';

COMMENT ON COLUMN "mime_type"."label" IS 'Label of this mime type';

COMMENT ON COLUMN "mime_type"."file_extension" IS 'File extensions for this mime type';

COMMENT ON TABLE "mime_type_map" IS 'Maps extensions to mime types';

COMMENT ON COLUMN "mime_type_map"."id" IS 'Unique identifier for the MIME type mapping.';

COMMENT ON COLUMN "mime_type_map"."extension" IS 'File extension, such as jpg or pdf';

COMMENT ON COLUMN "mime_type_map"."mime_type" IS 'MIME type associated with the file extension.';

COMMENT ON COLUMN "bank"."id" IS 'Unique identifier for the bank.';

COMMENT ON COLUMN "bank"."code" IS 'NIBSS institutionCode, a unique code identifying the bank.';

COMMENT ON COLUMN "bank"."name" IS 'Name of the Bank.';

COMMENT ON COLUMN "bank"."category" IS 'Bank Category, representing the category of the bank.';

COMMENT ON COLUMN "bank"."swift_code" IS 'SWIFT Code, a unique international bank identifier.';

COMMENT ON COLUMN "bank"."sort_code" IS 'SORT Code, a unique bank sorting code.';

COMMENT ON COLUMN "bank"."iban" IS 'IBAN Code, a unique international bank account number.';

COMMENT ON COLUMN "bank"."cust_care_phone" IS 'Contact phone number for customer care.';

COMMENT ON COLUMN "bank"."cust_care_email" IS 'Contact email for customer care.';

COMMENT ON COLUMN "bank"."escalation_contact" IS 'Contact information for escalation purposes.';

COMMENT ON COLUMN "doc_type"."id" IS 'Unique identifier for the document type.';

COMMENT ON COLUMN "doc_type"."name" IS 'Name or title of the document type e.g. Passport, Drivers License.';

COMMENT ON COLUMN "doc_type"."doc_category" IS 'category of this docunment';

COMMENT ON COLUMN "doc_type"."notes" IS 'Any additional remarks or details about the document type.';

COMMENT ON COLUMN "doc_type"."required_information" IS 'List or description of required fields/information for this document type.';

COMMENT ON COLUMN "doc_type"."is_serialized" IS 'Does this document type have a serial number';

COMMENT ON COLUMN "doc_type"."serial_length" IS 'Typical length of a serial number for this document type';

COMMENT ON COLUMN "doc_type"."expires" IS 'Does this type of document expire';

COMMENT ON COLUMN "doc_type"."validity_period" IS 'Standard validity duration of this type of document in days.';

COMMENT ON COLUMN "doc_type"."renewal_frequency" IS 'Frequency at which this document typically needs renewal, in days. Useful for setting reminders.';

COMMENT ON COLUMN "doc_type"."is_government_issued" IS 'Indicates if this document is typically issued by a government authority.';

COMMENT ON COLUMN "doc_type"."is_digital" IS 'Indicates if the document is typically in digital format.';

COMMENT ON COLUMN "doc_type"."template_url" IS 'URL or link to a template or sample of this document type, if available.';

COMMENT ON COLUMN "doc_type"."example_image_url" IS 'URL or link to an example image of this document type.';

COMMENT ON COLUMN "doc_type"."created_at" IS 'Timestamp when the document type was added to the system.';

COMMENT ON COLUMN "doc_type"."updated_at" IS 'Timestamp when the document type was last updated.';

COMMENT ON TABLE "agent_tier" IS 'Agent Tier';

COMMENT ON COLUMN "agent_tier"."id" IS 'Identity column - Unique identifier for the agent tier.';

COMMENT ON COLUMN "agent_tier"."name" IS 'Name of the agent tier - Descriptive name or title of the agent tier.';

COMMENT ON COLUMN "agent_tier"."notes" IS 'Additional notes or remarks about the agent tier, if necessary.';

COMMENT ON TABLE "user_ext" IS 'Additional data for user registration';

COMMENT ON COLUMN "user_ext"."id" IS 'Unique identifier for the user.';

COMMENT ON COLUMN "user_ext"."manager_id_fk" IS 'Manager ID - References the manager of the user, if applicable.';

COMMENT ON COLUMN "user_ext"."full_name" IS 'Middle name of the user, if available.';

COMMENT ON COLUMN "user_ext"."employee_number" IS 'Employee number assigned to the user, if applicable.';

COMMENT ON COLUMN "user_ext"."job_title" IS 'Job title or position of the user within the organization.';

COMMENT ON COLUMN "user_ext"."phone_number" IS 'Phone number for contacting the user.';

COMMENT ON COLUMN "user_ext"."email" IS 'Email address of the user, used for communication.';

COMMENT ON COLUMN "user_ext"."user_data" IS 'Additional user data or information, such as user preferences or details.';

COMMENT ON TABLE "agent" IS 'Agent Registration';

COMMENT ON COLUMN "agent"."id" IS 'Unique identifier for the agent.';

COMMENT ON COLUMN "agent"."aggregator_id_fk" IS 'References the aggregator agent if applicable.';

COMMENT ON COLUMN "agent"."is_aggregator" IS 'Indicates whether the agent is an aggregator.';

COMMENT ON COLUMN "agent"."became_aggregator_date" IS 'Timestamp when the agent became an aggregator, if applicable.';

COMMENT ON COLUMN "agent"."assigned_pos_count" IS 'Count of assigned point-of-sale (POS) devices.';

COMMENT ON COLUMN "agent"."aggregator_pos_threshold" IS 'Threshold for becoming an aggregator based on POS device count.';

COMMENT ON COLUMN "agent"."verification_status" IS 'The status of this agent, such as pending, active, etc.';

COMMENT ON COLUMN "agent"."verification_status_notes" IS 'Additional notes or remarks about the agents verification status.';

COMMENT ON COLUMN "agent"."agent_type" IS 'Type of agent, e.g., Individual, Business.';

COMMENT ON COLUMN "agent"."agent_role" IS 'Role of the agent, e.g., agent, sub-agent, aggregator.';

COMMENT ON COLUMN "agent"."agent_tier_id_fk" IS 'References the agents tier.';

COMMENT ON COLUMN "agent"."account_manager_id_fk" IS 'References the account manager responsible for this agent.';

COMMENT ON COLUMN "agent"."name" IS 'Name of the agent.';

COMMENT ON COLUMN "agent"."alias" IS 'Alias or alternate name for reporting purposes, if available.';

COMMENT ON COLUMN "agent"."phone_country_id_fk" IS 'References the country of the agents phone number.';

COMMENT ON COLUMN "agent"."phone" IS 'Primary phone number of the agent.';

COMMENT ON COLUMN "agent"."phone_ext" IS 'Extension for the primary phone number.';

COMMENT ON COLUMN "agent"."alt_phone_country_id_fk" IS 'References the country of the alternate phone number.';

COMMENT ON COLUMN "agent"."alt_phone" IS 'Alternate phone number for the agent.';

COMMENT ON COLUMN "agent"."alt_phone_ext" IS 'Extension for the alternate phone number.';

COMMENT ON COLUMN "agent"."email" IS 'Email address of the agent.';

COMMENT ON COLUMN "agent"."alt_email" IS 'Alternate email address for the agent.';

COMMENT ON COLUMN "agent"."bvn" IS 'Bank Verification Number (BVN) of the agent.';

COMMENT ON COLUMN "agent"."bvn_verified" IS 'Indicates whether the BVN is verified.';

COMMENT ON COLUMN "agent"."bvn_verification_date" IS 'Timestamp of BVN verification.';

COMMENT ON COLUMN "agent"."bvn_verification_code" IS 'Verification code for BVN.';

COMMENT ON COLUMN "agent"."tax_id" IS 'Tax identification number of the agent.';

COMMENT ON COLUMN "agent"."bank_id_fk" IS 'References the bank where the agent has an account.';

COMMENT ON COLUMN "agent"."bank_acc_no" IS 'Agent bank account number.';

COMMENT ON COLUMN "agent"."biz_name" IS 'Name of the agents business, if applicable.';

COMMENT ON COLUMN "agent"."biz_state_id_fk" IS 'References the state where the business is located.';

COMMENT ON COLUMN "agent"."biz_lga_id_fk" IS 'References the LGA where the business is located.';

COMMENT ON COLUMN "agent"."biz_city" IS 'City where the business is located.';

COMMENT ON COLUMN "agent"."biz_city_area" IS 'Specific area within the city where the business is located.';

COMMENT ON COLUMN "agent"."biz_street" IS 'Street address of the business.';

COMMENT ON COLUMN "agent"."biz_building" IS 'Building name or number of the business location.';

COMMENT ON COLUMN "agent"."biz_address" IS 'Detailed address information for the business.';

COMMENT ON COLUMN "agent"."biz_poa_img" IS 'Image of Proof of Address (POA) for the business.';

COMMENT ON COLUMN "agent"."biz_poa_desc" IS 'Description of the Proof of Address document.';

COMMENT ON COLUMN "agent"."biz_poa_valid" IS 'Indicates if the Proof of Address is valid.';

COMMENT ON COLUMN "agent"."biz_lat" IS 'Latitude coordinates of the business location.';

COMMENT ON COLUMN "agent"."biz_lon" IS 'Longitude coordinates of the business location.';

COMMENT ON COLUMN "agent"."biz_loc" IS 'Location description of the business.';

COMMENT ON COLUMN "agent"."biz_ggl_code" IS 'Google Maps code for the business location.';

COMMENT ON COLUMN "agent"."company_name" IS 'Name of the company associated with the agent.';

COMMENT ON COLUMN "agent"."cac_number" IS 'Corporate Affairs Commission (CAC) registration number.';

COMMENT ON COLUMN "agent"."cac_reg_date" IS 'Date of CAC registration.';

COMMENT ON COLUMN "agent"."cac_cert_img" IS 'Image of the CAC certificate.';

COMMENT ON COLUMN "agent"."cac_cert_no" IS 'Certificate number issued by CAC.';

COMMENT ON COLUMN "agent"."ref_code" IS 'Reference code associated with the agent.';

COMMENT ON COLUMN "agent"."access_pin" IS 'Access PIN for agent transactions.';

COMMENT ON COLUMN "agent"."registered_by_id_fk" IS 'References the user who registered the agent.';

COMMENT ON COLUMN "agent"."registration_date" IS 'Timestamp of agent registration.';

COMMENT ON COLUMN "agent"."reviewed_by_id_fk" IS 'References the user who reviewed the agent.';

COMMENT ON COLUMN "agent"."review_date" IS 'Timestamp of agent review.';

COMMENT ON COLUMN "agent"."approved_by_id_fk" IS 'References the user who approved the agent.';

COMMENT ON COLUMN "agent"."approval_date" IS 'Timestamp of agent approval.';

COMMENT ON COLUMN "agent"."approval_narrative" IS 'Narrative or notes related to agent approval.';

COMMENT ON COLUMN "agent"."kyc_submit_date" IS 'Timestamp of KYC document submission.';

COMMENT ON COLUMN "agent"."kyc_verification_status" IS 'KYC verification status, e.g., pending, approved.';

COMMENT ON COLUMN "agent"."kyc_approval_date" IS 'Timestamp of KYC document approval.';

COMMENT ON COLUMN "agent"."kyc_ref_code" IS 'Reference code associated with KYC.';

COMMENT ON COLUMN "agent"."kyc_rejection_narrative" IS 'Narrative or notes related to KYC rejection.';

COMMENT ON COLUMN "agent"."kyc_rejection_by_id_fk" IS 'References the user who rejected KYC.';

COMMENT ON COLUMN "agent"."rejection_date" IS 'Timestamp of agent rejection.';

COMMENT ON COLUMN "agent"."rejection_narrative" IS 'Narrative or notes related to agent rejection.';

COMMENT ON COLUMN "agent"."rejected_by_id_fk" IS 'References the user who rejected the agent.';

COMMENT ON COLUMN "agent"."face_matrix" IS 'Biometric data for face recognition.';

COMMENT ON COLUMN "agent"."finger_print_img" IS 'Image of fingerprint data.';

COMMENT ON COLUMN "agent"."agent_public_key" IS 'Public key for cryptographic operations.';

COMMENT ON COLUMN "agent"."agent_pj_expiry" IS 'Timestamp of public key expiration.';

COMMENT ON COLUMN "agent"."agent_history" IS 'Textual history of agent-related events.';

COMMENT ON TABLE "contact_type" IS 'phone, mobile, email, messaging, whatsapp, viber, instagram, website, etc';

COMMENT ON COLUMN "contact_type"."id" IS 'Unique identifier for the address type.';

COMMENT ON COLUMN "contact_type"."name" IS 'Name or type of contact method, e.g., Mobile, Email, WhatsApp.';

COMMENT ON COLUMN "contact_type"."description" IS 'Brief description about the address type, providing context or usage scenarios.';

COMMENT ON COLUMN "contact_type"."is_digital" IS 'Indicates if the contact method is digital or physical.';

COMMENT ON COLUMN "contact_type"."requires_verification" IS 'Indicates if the address type typically requires a verification process, e.g., email confirmation.';

COMMENT ON COLUMN "contact_type"."max_length" IS 'If applicable, the maximum character length of a value of this address type. Useful for validation.';

COMMENT ON COLUMN "contact_type"."icon_url" IS 'URL or link to an icon or image representing this address type. Useful for UI/UX purposes.';

COMMENT ON COLUMN "contact_type"."created_at" IS 'Timestamp when the address type was added to the system.';

COMMENT ON COLUMN "contact_type"."updated_at" IS 'Timestamp when the address type was last updated.';

COMMENT ON TABLE "contact" IS 'Agent or person contacts';

COMMENT ON COLUMN "contact"."id" IS 'Unique identifier for the contact.';

COMMENT ON COLUMN "contact"."person_id_fk" IS 'Reference to the individual associated with this contact.';

COMMENT ON COLUMN "contact"."agent_id_fk" IS 'Reference to the organization associated with this contact.';

COMMENT ON COLUMN "contact"."contact_type_id_fk" IS 'Reference to the type of contact.';

COMMENT ON COLUMN "contact"."contact" IS 'Actual contact value, e.g., phone number or email address.';

COMMENT ON COLUMN "contact"."priority" IS 'Ordering priority for displaying or using the contact. Lower value indicates higher priority.';

COMMENT ON COLUMN "contact"."best_time_to_contact_start" IS 'Preferred start time when the individual/organization is available for contact.';

COMMENT ON COLUMN "contact"."best_time_to_contact_end" IS 'Preferred end time for availability.';

COMMENT ON COLUMN "contact"."active_from_date" IS 'Date when this contact became active or relevant.';

COMMENT ON COLUMN "contact"."active_to_date" IS 'Date when this contact ceases to be active or relevant.';

COMMENT ON COLUMN "contact"."for_business_use" IS 'Indicates if the contact is primarily for business purposes.';

COMMENT ON COLUMN "contact"."for_personal_use" IS 'Indicates if the contact is primarily for personal use.';

COMMENT ON COLUMN "contact"."do_not_use" IS 'Indicates if there are any restrictions or requests not to use this contact.';

COMMENT ON COLUMN "contact"."is_active" IS 'Indicates if this contact is currently active and usable.';

COMMENT ON COLUMN "contact"."is_blocked" IS 'Indicates if this contact is blocked, maybe due to spam or other reasons.';

COMMENT ON COLUMN "contact"."is_verified" IS 'Indicates if this contact has been verified, e.g., via OTP or email confirmation.';

COMMENT ON COLUMN "contact"."notes" IS 'Additional notes or context about the contact.';

COMMENT ON TABLE "agent_person_link" IS 'People associated with an Agent';

COMMENT ON COLUMN "agent_person_link"."person_id_fk" IS 'Foreign key reference to the person linked to the agent.';

COMMENT ON COLUMN "agent_person_link"."agent_id_fk" IS 'Foreign key reference to the agent linked to the person.';

COMMENT ON TABLE "person" IS 'People who work for an Agent, Bank or Others';

COMMENT ON COLUMN "person"."id" IS 'Unique identifier for the person.';

COMMENT ON COLUMN "person"."agent_id_fk" IS 'References the associated agent if applicable.';

COMMENT ON COLUMN "person"."next_of_kin_id_fk" IS 'References the next of kin for this person, if applicable.';

COMMENT ON COLUMN "person"."person_role" IS 'Role or type of person, e.g., customer, contact.';

COMMENT ON COLUMN "person"."first_name" IS 'First name of the person.';

COMMENT ON COLUMN "person"."middle_name" IS 'Middle name of the person.';

COMMENT ON COLUMN "person"."surname" IS 'Last name or surname of the person.';

COMMENT ON COLUMN "person"."nick_name" IS 'Nickname or alias of the person.';

COMMENT ON COLUMN "person"."gender" IS 'Gender of the person, e.g., Male, Female.';

COMMENT ON COLUMN "person"."photo_img" IS 'Image of the person.';

COMMENT ON COLUMN "person"."signature_img" IS 'Image of the persons signature.';

COMMENT ON COLUMN "person"."bvn_no" IS 'Bank Verification Number (BVN) of the person.';

COMMENT ON COLUMN "person"."bvn_verified" IS 'Indicates whether the BVN is verified.';

COMMENT ON COLUMN "person"."bvn_verification_date" IS 'Timestamp of BVN verification.';

COMMENT ON COLUMN "person"."bvn_verification_code" IS 'Verification code for BVN.';

COMMENT ON COLUMN "person"."tax_id" IS 'Tax identification number of the person.';

COMMENT ON COLUMN "person"."home_poa_img" IS 'Image of Proof of Address (POA) for the home address.';

COMMENT ON COLUMN "person"."home_poa_desc" IS 'Description of the Proof of Address document for the home address.';

COMMENT ON COLUMN "person"."home_poa_valid" IS 'Indicates if the Proof of Address for the home is valid.';

COMMENT ON COLUMN "person"."home_lat" IS 'Latitude coordinates of the home address.';

COMMENT ON COLUMN "person"."home_lon" IS 'Longitude coordinates of the home address.';

COMMENT ON COLUMN "person"."home_loc" IS 'Location description of the home address.';

COMMENT ON COLUMN "person"."home_ggl_code" IS 'Google Maps code for the home address.';

COMMENT ON TABLE "person_admin_data" IS 'Additional information on How to communicate and handle a persons data';

COMMENT ON COLUMN "person_admin_data"."person_id_fk" IS 'References the associated person.';

COMMENT ON COLUMN "person_admin_data"."creation_time" IS 'Timestamp when the data was created.';

COMMENT ON COLUMN "person_admin_data"."failed_login_count" IS 'Count of failed login attempts.';

COMMENT ON COLUMN "person_admin_data"."failed_login_timestamp" IS 'Timestamp of the last failed login attempt.';

COMMENT ON COLUMN "person_admin_data"."password_last_set_time" IS 'Timestamp when the password was last set.';

COMMENT ON COLUMN "person_admin_data"."profile_picture" IS 'URL or path to the profile picture.';

COMMENT ON COLUMN "person_admin_data"."awatar" IS 'URL or path to the avatar.';

COMMENT ON COLUMN "person_admin_data"."screen_name" IS 'Screen name or username.';

COMMENT ON COLUMN "person_admin_data"."user_priv_cert" IS 'Users private certificate.';

COMMENT ON COLUMN "person_admin_data"."user_pub_cert" IS 'Users public certificate.';

COMMENT ON COLUMN "person_admin_data"."alt_security_identities" IS 'Alternate security identities.';

COMMENT ON COLUMN "person_admin_data"."generated_UID" IS 'Generated unique identifier.';

COMMENT ON COLUMN "person_admin_data"."do_not_email" IS 'Indicates if email communication is prohibited.';

COMMENT ON COLUMN "person_admin_data"."do_not_phone" IS 'Indicates if phone communication is prohibited.';

COMMENT ON COLUMN "person_admin_data"."do_not_mail" IS 'Indicates if physical mail communication is prohibited.';

COMMENT ON COLUMN "person_admin_data"."do_not_sms" IS 'Indicates if SMS communication is prohibited.';

COMMENT ON COLUMN "person_admin_data"."do_not_trade" IS 'Indicates if trading is prohibited.';

COMMENT ON COLUMN "person_admin_data"."opted_out" IS 'Indicates if the user has opted out of certain activities.';

COMMENT ON COLUMN "person_admin_data"."do_not_track_update_date" IS 'Date when tracking was disabled.';

COMMENT ON COLUMN "person_admin_data"."do_not_process_from_update_date" IS 'Date when processing was disabled.';

COMMENT ON COLUMN "person_admin_data"."do_not_market_from_update_date" IS 'Date when marketing was disabled.';

COMMENT ON COLUMN "person_admin_data"."do_not_track_location_update_date" IS 'Date when location tracking was disabled.';

COMMENT ON COLUMN "person_admin_data"."do_not_profile_from_update_date" IS 'Date when profiling was disabled.';

COMMENT ON COLUMN "person_admin_data"."do_forget_me_from_update_date" IS 'Date when -forget me- request was processed.';

COMMENT ON COLUMN "person_admin_data"."do_not_process_reason" IS 'Reason for not processing data.';

COMMENT ON COLUMN "person_admin_data"."no_merge_reason" IS 'Reason for not merging data.';

COMMENT ON COLUMN "person_admin_data"."do_extract_my_data_update_date" IS 'Date when data extraction request was processed.';

COMMENT ON COLUMN "person_admin_data"."should_forget" IS 'Indicates if data should be forgotten.';

COMMENT ON COLUMN "person_admin_data"."consumer_credit_score_provider_name" IS 'Name of the consumer credit score provider.';

COMMENT ON COLUMN "person_admin_data"."web_site_url" IS 'URL of the website.';

COMMENT ON COLUMN "person_admin_data"."ordering_name" IS 'Name used for ordering.';

COMMENT ON COLUMN "person_admin_data"."hospitalizations_last5_years_count" IS 'Count of hospitalizations in the last 5 years.';

COMMENT ON COLUMN "person_admin_data"."surgeries_last5_years_count" IS 'Count of surgeries in the last 5 years.';

COMMENT ON COLUMN "person_admin_data"."dependent_count" IS 'Count of dependents.';

COMMENT ON COLUMN "person_admin_data"."account_locked" IS 'Indicates if the account is locked.';

COMMENT ON COLUMN "person_admin_data"."send_individual_data" IS 'Indicates if individual data should be sent.';

COMMENT ON COLUMN "person_admin_data"."influencer_rating" IS 'Influencer rating.';

COMMENT ON TABLE "agent_doc_link" IS 'An Agents Documents';

COMMENT ON COLUMN "agent_doc_link"."agent_id_fk" IS 'Foreign key reference to the agent whose document is linked.';

COMMENT ON COLUMN "agent_doc_link"."doc_id_fk" IS 'Foreign key reference to the document being linked.';

COMMENT ON COLUMN "agent_doc_link"."verification_status" IS 'Status of document verification, with a default value of _pending_.';

COMMENT ON COLUMN "agent_doc_link"."submit_date" IS 'Timestamp when the document is submitted, with a default value of the current timestamp.';

COMMENT ON COLUMN "agent_doc_link"."notes" IS 'Additional notes or comments related to the document link.';

COMMENT ON TABLE "person_doc_link" IS 'A Persons Documents';

COMMENT ON COLUMN "person_doc_link"."person_id_fk" IS 'Foreign key reference to the person whose document is linked.';

COMMENT ON COLUMN "person_doc_link"."doc_id_fk" IS 'Foreign key reference to the document being linked.';

COMMENT ON COLUMN "person_doc_link"."verification_status" IS 'Status of document verification, with a default value of _pending_.';

COMMENT ON COLUMN "person_doc_link"."submit_date" IS 'Timestamp when the document is submitted, with a default value of the current timestamp.';

COMMENT ON TABLE "doc" IS 'Document Archives';

COMMENT ON COLUMN "doc"."id" IS 'Unique identifier for the document.';

COMMENT ON COLUMN "doc"."doc_type_id_fk" IS 'References the type of document e.g. passport, license.';

COMMENT ON COLUMN "doc"."person_id_fk" IS 'The person to whom the document belongs.';

COMMENT ON COLUMN "doc"."agent_id_fk" IS 'The organization associated with the document.';

COMMENT ON COLUMN "doc"."doc_front_img" IS 'Image of the front of the document';

COMMENT ON COLUMN "doc"."doc_back_img" IS 'Image of the back of the document';

COMMENT ON COLUMN "doc"."doc_name" IS 'Name or title of the document.';

COMMENT ON COLUMN "doc"."doc_content_type_id_fk" IS 'MIME type of the document content e.g. application/pdf, image/jpeg.';

COMMENT ON COLUMN "doc"."doc_url" IS 'Actual doc in pdf or other format';

COMMENT ON COLUMN "doc"."doc_length" IS 'Size of the document in bytes or another measure.';

COMMENT ON COLUMN "doc"."doc_text" IS 'Text content extracted from the document. Useful for search and analytics. May be stored in another database for scalability.';

COMMENT ON COLUMN "doc"."identification_number" IS 'Unique identification number, e.g., passport number.';

COMMENT ON COLUMN "doc"."serial_number" IS 'Serial number of the document if applicable.';

COMMENT ON COLUMN "doc"."description" IS 'Detailed description or remarks about the document.';

COMMENT ON COLUMN "doc"."file_name" IS 'Name of the file if stored digitally.';

COMMENT ON COLUMN "doc"."page_count" IS 'Number of pages in the document, if applicable.';

COMMENT ON COLUMN "doc"."issued_on" IS 'The date when the document was issued.';

COMMENT ON COLUMN "doc"."issued_by_authority" IS 'Authority or organization that issued the document.';

COMMENT ON COLUMN "doc"."issued_at" IS 'Place or location where the document was issued.';

COMMENT ON COLUMN "doc"."expires_on" IS 'Expiration date of the document.';

COMMENT ON COLUMN "doc"."is_expired" IS 'Flag to indicate if the document has expired.';

COMMENT ON COLUMN "doc"."verification_date" IS 'The date when the document was verified.';

COMMENT ON COLUMN "doc"."uploaded_on" IS 'Timestamp when the document was uploaded into the system.';

COMMENT ON COLUMN "doc"."updated_on" IS 'Timestamp when the document record was last updated.';

COMMENT ON TABLE "pos" IS 'Points-of-Sale';

COMMENT ON COLUMN "pos"."id" IS 'Unique identifier for the Point of Sale (PoS).';

COMMENT ON COLUMN "pos"."serial_no" IS 'Unique serial number for the PoS.';

COMMENT ON COLUMN "pos"."imei" IS 'IMEI number of the PoS, if applicable.';

COMMENT ON COLUMN "pos"."mac_addr" IS 'MAC address of the PoS.';

COMMENT ON COLUMN "pos"."device_model" IS 'Model of the PoS device.';

COMMENT ON COLUMN "pos"."device_make" IS 'Make or manufacturer of the PoS device.';

COMMENT ON COLUMN "pos"."device_mfg" IS 'Manufacturer of the PoS device.';

COMMENT ON COLUMN "pos"."os_version" IS 'Operating system version of the PoS.';

COMMENT ON COLUMN "pos"."device_color" IS 'Color of the PoS device.';

COMMENT ON COLUMN "pos"."device_condition" IS 'Condition of the PoS device (e.g., working, irreparable, repaired).';

COMMENT ON COLUMN "pos"."status" IS 'Current status of the PoS.';

COMMENT ON COLUMN "pos"."owner_type" IS 'Type of owner of the PoS.';

COMMENT ON COLUMN "pos"."registration_date" IS 'Timestamp when the PoS was registered.';

COMMENT ON COLUMN "pos"."assigned" IS 'Indicates if the PoS is assigned.';

COMMENT ON COLUMN "pos"."assigned_date" IS 'Timestamp when the PoS was assigned.';

COMMENT ON COLUMN "pos"."assigned_narrative" IS 'Narrative or description of the assignment.';

COMMENT ON COLUMN "pos"."active" IS 'Indicates if the PoS is active.';

COMMENT ON COLUMN "pos"."activation_date" IS 'Timestamp when the PoS was activated.';

COMMENT ON COLUMN "pos"."last_active" IS 'Timestamp of the last activity.';

COMMENT ON COLUMN "pos"."deployed" IS 'Indicates if the PoS is deployed.';

COMMENT ON COLUMN "pos"."deploy_date" IS 'Timestamp when the PoS was deployed.';

COMMENT ON COLUMN "pos"."deploy_narrative" IS 'Narrative or description of the deployment.';

COMMENT ON COLUMN "pos"."returned" IS 'Indicates if the PoS was returned.';

COMMENT ON COLUMN "pos"."return_date" IS 'Timestamp when the PoS was returned.';

COMMENT ON COLUMN "pos"."return_narrative" IS 'Narrative or description of the return.';

COMMENT ON COLUMN "pos"."return_received_date" IS 'Timestamp when the return was received.';

COMMENT ON COLUMN "pos"."return_received_by_id_fk" IS 'Reference to the user who received the return.';

COMMENT ON COLUMN "pos"."state_id_fk" IS 'Reference to the state where the PoS is deployed.';

COMMENT ON COLUMN "pos"."lga_id_fk" IS 'Reference to the local government area where the PoS is deployed.';

COMMENT ON COLUMN "pos"."street_address" IS 'Street address of the PoS deployment location.';

COMMENT ON COLUMN "pos"."building_name" IS 'Name of the building where the PoS is deployed.';

COMMENT ON COLUMN "pos"."contact_phone_num" IS 'Contact phone number for the PoS deployment location.';

COMMENT ON COLUMN "pos"."pos_user" IS 'User associated with the PoS.';

COMMENT ON COLUMN "pos"."crypt_priv_key" IS 'Private key for cryptographic operations.';

COMMENT ON COLUMN "pos"."crypt_pub_key" IS 'Public key for cryptographic operations.';

COMMENT ON COLUMN "pos"."crypt_password" IS 'Password for cryptographic operations.';

COMMENT ON COLUMN "pos"."override_key" IS 'Override key for cryptographic operations.';

COMMENT ON TABLE "agent_pos_link" IS 'Records the assignment of a Point of Sale (PoS) to an agent.';

COMMENT ON COLUMN "agent_pos_link"."agent_id_fk" IS 'Foreign key reference to the agent to whom the PoS is assigned.';

COMMENT ON COLUMN "agent_pos_link"."pos_id_fk" IS 'Foreign key reference to the Point of Sale (PoS) being assigned.';

COMMENT ON COLUMN "agent_pos_link"."assigned_date" IS 'Timestamp when the PoS is assigned.';

COMMENT ON COLUMN "agent_pos_link"."assigned_by" IS 'User who assigned the PoS to the agent.';

COMMENT ON COLUMN "agent_pos_link"."received_by" IS 'User who received the PoS.';

COMMENT ON COLUMN "agent_pos_link"."received_date" IS 'Timestamp when the PoS is received by the agent.';

COMMENT ON COLUMN "agent_pos_link"."received_location" IS 'Location where the PoS is received.';

COMMENT ON COLUMN "agent_pos_link"."delivery_note" IS 'Delivery note associated with the PoS assignment.';

COMMENT ON COLUMN "agent_pos_link"."delivery_note_printed" IS 'Indicates whether the delivery note has been printed.';

COMMENT ON COLUMN "agent_pos_link"."activated" IS 'Indicates whether the PoS has been activated.';

COMMENT ON COLUMN "agent_pos_link"."activation_date" IS 'Timestamp when the PoS is activated.';

COMMENT ON COLUMN "agent_pos_link"."activation_otp" IS 'One-Time Password (OTP) used for activation.';

COMMENT ON COLUMN "agent_pos_link"."otp_sent" IS 'Indicates whether the OTP has been sent.';

COMMENT ON COLUMN "agent_pos_link"."otp_sent_time" IS 'Timestamp when the OTP is sent.';

COMMENT ON COLUMN "agent_pos_link"."otp_used" IS 'Indicates whether the OTP has been used for activation.';

COMMENT ON COLUMN "agent_pos_link"."history" IS 'Text field to store the history or additional information about the PoS assignment.';

COMMENT ON TABLE "token_provider" IS 'Connection parameters for differnt providers';

COMMENT ON COLUMN "token_provider"."id" IS 'Unique identifier for the token provider.';

COMMENT ON COLUMN "token_provider"."name" IS 'Name of the token provider.';

COMMENT ON COLUMN "token_provider"."notes" IS 'Additional notes or remarks about the token provider.';

COMMENT ON COLUMN "token_provider"."priv_key" IS 'Private key used for authentication and encryption.';

COMMENT ON COLUMN "token_provider"."pub_key" IS 'Public key used for authentication and encryption.';

COMMENT ON COLUMN "token_provider"."endpoint" IS 'Endpoint URL for communication with the token provider.';

COMMENT ON COLUMN "token_provider"."protocol" IS 'Communication protocol used with the token provider (e.g., HTTPS).';

COMMENT ON COLUMN "token_provider"."auth" IS 'Authentication mechanism or credentials required for access.';

COMMENT ON COLUMN "token_provider"."ssl" IS 'SSL/TLS configuration or settings for secure communication.';

COMMENT ON COLUMN "token_provider"."ip_whitelist" IS 'List of whitelisted IP addresses for accessing the token provider.';

COMMENT ON COLUMN "token_provider"."password" IS 'Password associated with the token provider.';

COMMENT ON COLUMN "token_provider"."enabled" IS 'Indicates if the token provider is enabled or disabled.';

COMMENT ON COLUMN "token"."id" IS 'Unique identifier for the token.';

COMMENT ON COLUMN "token"."token_provider_id_fk" IS 'Foreign key referencing the associated token provider.';

COMMENT ON COLUMN "token"."token_name" IS 'Name or identifier for the token.';

COMMENT ON COLUMN "token"."token_issue_date" IS 'Timestamp when the token was issued.';

COMMENT ON COLUMN "token"."token_expiry_date" IS 'Timestamp when the token expires.';

COMMENT ON COLUMN "token"."token_validity" IS 'Duration of token validity in seconds.';

COMMENT ON COLUMN "token"."token_expired" IS 'Indicates if the token has expired.';

COMMENT ON COLUMN "token"."token_value" IS 'Actual token value or token string.';

COMMENT ON COLUMN "token"."token_username" IS 'Username associated with the token.';

COMMENT ON COLUMN "token"."token_password" IS 'Password associated with the token.';

COMMENT ON COLUMN "token"."token_notes" IS 'Additional notes or remarks about the token.';

COMMENT ON COLUMN "token"."token_client_secret" IS 'Client secret associated with the token.';

COMMENT ON COLUMN "token"."enabled" IS 'Indicates if the token is enabled or disabled.';

COMMENT ON TABLE "biller_category" IS 'Category of Biller';

COMMENT ON COLUMN "biller_category"."id" IS 'Unique identifier for the biller category.';

COMMENT ON COLUMN "biller_category"."name" IS 'Name or title of the biller category.';

COMMENT ON COLUMN "biller_category"."notes" IS 'Additional notes or remarks about the biller category.';

COMMENT ON COLUMN "biller"."id" IS 'Unique identifier for the biller.';

COMMENT ON COLUMN "biller"."category_id_fk" IS 'Foreign key referencing the biller category to which this biller belongs.';

COMMENT ON COLUMN "biller"."code" IS 'Unique code or identifier for the biller.';

COMMENT ON COLUMN "biller"."name" IS 'Name or title of the biller.';

COMMENT ON COLUMN "biller"."url" IS 'URL or link associated with the biller.';

COMMENT ON COLUMN "biller"."note" IS 'Additional notes or remarks about the biller.';

COMMENT ON COLUMN "biller_offering"."biller_id_fk" IS 'Foreign key referencing the biller to which this offering belongs.';

COMMENT ON COLUMN "biller_offering"."id" IS 'Unique identifier for the biller offering.';

COMMENT ON COLUMN "biller_offering"."name" IS 'Name or title of the biller offering.';

COMMENT ON COLUMN "biller_offering"."description" IS 'Description of the biller offering.';

COMMENT ON COLUMN "biller_offering"."price" IS 'Price or cost associated with the biller offering.';

COMMENT ON COLUMN "trans_type"."id" IS 'Unique identifier for the transaction type.';

COMMENT ON COLUMN "trans_type"."name" IS 'Name or title of the transaction type, e.g., Deposit, Withdrawal, Transfer, Bill Payment, etc.';

COMMENT ON COLUMN "trans_type"."notes" IS 'Additional notes or descriptions related to the transaction type.';

COMMENT ON COLUMN "customer_segment"."id" IS 'Unique identifier for the customer segment.';

COMMENT ON COLUMN "customer_segment"."name" IS 'Name or title of the customer segment.';

COMMENT ON COLUMN "customer_segment"."notes" IS 'Additional notes or descriptions related to the customer segment.';

COMMENT ON TABLE "risk_profile" IS 'Risk associated with financial transactions';

COMMENT ON COLUMN "risk_profile"."id" IS 'Unique identifier for each risk profile';

COMMENT ON COLUMN "risk_profile"."name" IS 'Name of the risk profile';

COMMENT ON COLUMN "risk_profile"."description" IS 'Detailed description of the risk profile';

COMMENT ON COLUMN "risk_profile"."risk_score" IS 'Quantitative measure of risk, often based on a specific scoring system';

COMMENT ON COLUMN "risk_profile"."risk_category" IS 'Categorization of risk (e.g., Low, Moderate, High)';

COMMENT ON COLUMN "risk_profile"."max_acceptable_loss" IS 'Maximum financial loss that is acceptable for this risk profile, usually a percentage or monetary value';

COMMENT ON COLUMN "risk_profile"."probability_of_loss" IS 'Likelihood of incurring a loss, often expressed as a percentage';

COMMENT ON COLUMN "risk_profile"."historical_volatility" IS 'Measure of the variation in the price of the asset over time';

COMMENT ON COLUMN "risk_profile"."liquidity_rating" IS 'Rating representing the ease of converting the asset to cash without significant loss of value';

COMMENT ON COLUMN "risk_profile"."regulatory_compliance" IS 'Indication of any specific regulatory compliance considerations relevant to the risk profile';

COMMENT ON COLUMN "risk_profile"."market_sensitivity" IS 'Measure of how sensitive the asset is to market fluctuations';

COMMENT ON COLUMN "risk_profile"."credit_rating" IS 'Creditworthiness of a debtor, particularly relevant in the context of credit risk';

COMMENT ON COLUMN "risk_profile"."investment_horizon" IS 'Expected duration for holding the investment';

COMMENT ON COLUMN "risk_profile"."sector_exposure" IS 'Indicates the sectors to which the investment is exposed';

COMMENT ON COLUMN "risk_profile"."geographic_exposure" IS 'Highlights the geographical regions involved in the transaction';

COMMENT ON COLUMN "commission"."id" IS 'Unique identifier for the commission reference.';

COMMENT ON COLUMN "commission"."agent_type" IS 'Type of agent, e.g., Individual, Business, etc.';

COMMENT ON COLUMN "commission"."agent_tier_level_id_fk" IS 'Foreign key to the agent tier level if applicable.';

COMMENT ON COLUMN "commission"."agent_id_fk" IS 'Foreign key to the agent associated with this commission reference.';

COMMENT ON COLUMN "commission"."state_id_fk" IS 'Foreign key to the state if applicable.';

COMMENT ON COLUMN "commission"."lga_id_fk" IS 'Foreign key to the local government area if applicable.';

COMMENT ON COLUMN "commission"."currency_id_fk" IS 'Commission of specfic currencies, defaults to NGN';

COMMENT ON COLUMN "commission"."risk_profile_id_fk" IS 'Risk associated with financial transactions';

COMMENT ON COLUMN "commission"."biller_id_fk" IS 'Foreign key to the biller associated with this commission reference.';

COMMENT ON COLUMN "commission"."biller_offering_id_fk" IS 'Foreign key to the biller offering associated with this commission reference.';

COMMENT ON COLUMN "commission"."transaction_type_id_fk" IS 'Foreign key to the transaction type if applicable.';

COMMENT ON COLUMN "commission"."customer_segment_id_fk" IS 'Foreign key to the customer segment.';

COMMENT ON COLUMN "commission"."special_promotion_id_fk" IS 'Foreign key to the special promotion if applicable.';

COMMENT ON COLUMN "commission"."min_trans_amount" IS 'Minimum transaction amount for commission calculation.';

COMMENT ON COLUMN "commission"."max_trans_amount" IS 'Maximum transaction amount for commission calculation.';

COMMENT ON COLUMN "commission"."min_max_step" IS 'Step value for minimum and maximum transaction amounts.';

COMMENT ON COLUMN "commission"."min_comm_amount" IS 'Minimum commission amount.';

COMMENT ON COLUMN "commission"."max_comm_amount" IS 'Maximum commission amount.';

COMMENT ON COLUMN "commission"."commission_rate" IS 'Commission rate in percentage.';

COMMENT ON COLUMN "commission"."start_time" IS 'Start time of commission rate validity.';

COMMENT ON COLUMN "commission"."end_time" IS 'End time of commission rate validity.';

COMMENT ON COLUMN "commission"."start_date" IS 'Start date of commission rate validity (if applicable).';

COMMENT ON COLUMN "commission"."end_date" IS 'End date of commission rate validity (if applicable).';

COMMENT ON COLUMN "promotion"."id" IS 'Unique identifier for the promotion.';

COMMENT ON COLUMN "promotion"."name" IS 'Name or title of the promotion.';

COMMENT ON COLUMN "promotion"."notes" IS 'Additional remarks or details about the promotion.';

COMMENT ON COLUMN "promotion"."start_date" IS 'Start date of the promotion.';

COMMENT ON COLUMN "promotion"."end_date" IS 'End date of the promotion.';

COMMENT ON COLUMN "currency"."id" IS 'Unique identifier for the currency.';

COMMENT ON COLUMN "currency"."name" IS 'Short name or code of the currency.';

COMMENT ON COLUMN "currency"."symbol" IS 'Symbol representing the currency.';

COMMENT ON COLUMN "currency"."numeric_code" IS 'Numeric code for the currency.';

COMMENT ON COLUMN "currency"."full_name" IS 'Full name or description of the currency.';

COMMENT ON COLUMN "currency"."decimal_places" IS 'Number of decimal places for the currency.';

COMMENT ON COLUMN "currency"."internationalized_name_code" IS 'Code for the internationalized name of the currency.';

COMMENT ON COLUMN "trans_routing_threshold"."id" IS 'Unique identifier for the threshold.';

COMMENT ON COLUMN "trans_routing_threshold"."name" IS 'Name or description of the threshold.';

COMMENT ON COLUMN "trans_routing_threshold"."min_amount" IS 'Minimum transaction amount that triggers this threshold.';

COMMENT ON COLUMN "trans_routing_threshold"."max_amount" IS 'Maximum transaction amount that triggers this threshold.';

COMMENT ON COLUMN "trans_routing_threshold"."priority" IS 'Priority level for this threshold.';

COMMENT ON TABLE "transaction" IS 'Table of Transactions';

COMMENT ON COLUMN "transaction"."id" IS 'Unique identifier for the transaction.';

COMMENT ON COLUMN "transaction"."coupon_id_fk" IS 'Reference to the associated coupon, if applicable.';

COMMENT ON COLUMN "transaction"."customer_name" IS 'Name of the customer involved in the transaction.';

COMMENT ON COLUMN "transaction"."trans_purpose" IS 'Description of the transaction purpose.';

COMMENT ON COLUMN "transaction"."customer_id" IS 'Identifier for the customer.';

COMMENT ON COLUMN "transaction"."transaction_type" IS 'Type of transaction (e.g., withdrawal, deposit).';

COMMENT ON COLUMN "transaction"."card_trans_type" IS 'Type of card transaction (e.g., purchase).';

COMMENT ON COLUMN "transaction"."agent_id_fk" IS 'Merchant ID.';

COMMENT ON COLUMN "transaction"."payment_card_id_fk" IS 'Reference to the payment card used.';

COMMENT ON COLUMN "transaction"."pos_id_fk" IS 'Point of Sale (PoS) ID.';

COMMENT ON COLUMN "transaction"."wallet_id_fk" IS 'Reference to the wallet used.';

COMMENT ON COLUMN "transaction"."biller_id_fk" IS 'Reference to the biller involved.';

COMMENT ON COLUMN "transaction"."biller_offering_id_fk" IS 'Reference to the biller offering used.';

COMMENT ON COLUMN "transaction"."trans_time" IS 'Timestamp of the transaction.';

COMMENT ON COLUMN "transaction"."currency_id_fk" IS 'Reference to the currency used.';

COMMENT ON COLUMN "transaction"."trans_status" IS 'Status of the transaction (e.g., pending, completed).';

COMMENT ON COLUMN "transaction"."trans_route_id_fk" IS 'Reference to the routing threshold used.';

COMMENT ON COLUMN "transaction"."origin_source" IS 'Source of funds for the transaction.';

COMMENT ON COLUMN "transaction"."origin_ref_code" IS 'Reference code associated with the origin of the transaction.';

COMMENT ON COLUMN "transaction"."origin_trans_notes" IS 'Additional notes about the origin of the transaction.';

COMMENT ON COLUMN "transaction"."origin_bank_id_fk" IS 'Reference to the originating bank, if applicable.';

COMMENT ON COLUMN "transaction"."origin_institution_code" IS 'Institution code for the origin.';

COMMENT ON COLUMN "transaction"."origin_account_num" IS 'Account number associated with the origin.';

COMMENT ON COLUMN "transaction"."origin_account_name" IS 'Account name associated with the origin.';

COMMENT ON COLUMN "transaction"."origin_KYC_Level" IS 'KYC (Know Your Customer) level of the origin.';

COMMENT ON COLUMN "transaction"."origin_Bank_Verification_Number" IS 'Bank Verification Number associated with the origin.';

COMMENT ON COLUMN "transaction"."origin_bvn" IS 'Used for checking balance of the origin.';

COMMENT ON COLUMN "transaction"."session_ref" IS 'Reference to the session related to the transaction.';

COMMENT ON COLUMN "transaction"."transaction_ref" IS 'Reference code for the transaction.';

COMMENT ON COLUMN "transaction"."channelCode" IS 'Code identifying the transaction channel.';

COMMENT ON COLUMN "transaction"."name_enquiry_ref" IS 'Reference code for name inquiry related to the transaction.';

COMMENT ON COLUMN "transaction"."api_transactionid" IS 'API transaction ID.';

COMMENT ON COLUMN "transaction"."receipt_no" IS 'Receipt number associated with the transaction.';

COMMENT ON COLUMN "transaction"."pin_based" IS 'Whether the transaction is PIN-based.';

COMMENT ON COLUMN "transaction"."pin_code" IS 'PIN code associated with the transaction.';

COMMENT ON COLUMN "transaction"."pin_option" IS 'PIN option for the transaction.';

COMMENT ON COLUMN "transaction"."authorization_code" IS 'Authorization code for the transaction.';

COMMENT ON COLUMN "transaction"."acquirer_name" IS 'Name of the acquirer.';

COMMENT ON COLUMN "transaction"."currency" IS 'Currency used for the transaction.';

COMMENT ON COLUMN "transaction"."transaction_location" IS 'Location where the transaction occurred.';

COMMENT ON COLUMN "transaction"."payment_reference" IS 'Reference code for the payment.';

COMMENT ON COLUMN "transaction"."response_code" IS 'Response code related to the transaction.';

COMMENT ON COLUMN "transaction"."trans_dest" IS 'Destination of funds for the transaction.';

COMMENT ON COLUMN "transaction"."bene_ref_code" IS 'Reference code associated with the beneficiary.';

COMMENT ON COLUMN "transaction"."bene_trans_notes" IS 'Additional notes about the beneficiary.';

COMMENT ON COLUMN "transaction"."bene_bank_id_fk" IS 'Reference to the beneficiary bank, if applicable.';

COMMENT ON COLUMN "transaction"."bene_account_num" IS 'Account number associated with the beneficiary.';

COMMENT ON COLUMN "transaction"."bene_institution_code" IS 'Institution code for the beneficiary.';

COMMENT ON COLUMN "transaction"."bene_bank_verification_number" IS 'Bank Verification Number associated with the beneficiary.';

COMMENT ON COLUMN "transaction"."bene_KYC_Level" IS 'KYC (Know Your Customer) level of the beneficiary.';

COMMENT ON COLUMN "transaction"."bene_account_name" IS 'Account name associated with the beneficiary.';

COMMENT ON COLUMN "transaction"."bene_phone_number" IS 'Phone number associated with the beneficiary.';

COMMENT ON COLUMN "transaction"."bene_phone_denom" IS 'Denomination of the beneficiary phone.';

COMMENT ON COLUMN "transaction"."bene_phone_product" IS 'Product associated with the beneficiary phone.';

COMMENT ON COLUMN "transaction"."transaction_amount" IS 'Amount of the transaction.';

COMMENT ON COLUMN "transaction"."available_balance" IS 'Available balance for the transaction.';

COMMENT ON COLUMN "transaction"."svc_fees" IS 'Service fees associated with the transaction.';

COMMENT ON COLUMN "transaction"."comm_total" IS 'Total commission amount for the transaction.';

COMMENT ON COLUMN "transaction"."comm_agent" IS 'Commission amount for the agent.';

COMMENT ON COLUMN "transaction"."comm_aggr" IS 'Commission amount for the aggregator.';

COMMENT ON COLUMN "transaction"."comm_ours" IS 'Commission amount for us.';

COMMENT ON COLUMN "transaction"."comm_other" IS 'Payments to others associated with the transaction.';

COMMENT ON COLUMN "transaction"."comm_net_pct" IS 'Net commission percentage.';

COMMENT ON COLUMN "transaction"."tax" IS 'Tax amount associated with the transaction.';

COMMENT ON COLUMN "transaction"."excise_duty" IS 'Excise duty amount.';

COMMENT ON COLUMN "transaction"."vat" IS 'Value-added tax (VAT) amount.';

COMMENT ON COLUMN "transaction"."transmit_amount" IS 'Transmit amount for the transaction.';

COMMENT ON COLUMN "transaction"."comm_narration" IS 'Narration describing how the commission was calculated.';

COMMENT ON COLUMN "transaction"."trans_currency" IS 'Currency code for the transaction.';

COMMENT ON COLUMN "transaction"."trans_convert_currency" IS 'Currency for currency conversion, if applicable.';

COMMENT ON COLUMN "transaction"."trans_currency_exchange_rate" IS 'Exchange rate for currency conversion.';

COMMENT ON COLUMN "transaction"."trans_date" IS 'Timestamp of the transaction date.';

COMMENT ON COLUMN "transaction"."customer_segment_id_fk" IS 'Reference to the customer segment.';

COMMENT ON COLUMN "transaction"."agent_tier_level_id_fk" IS 'Reference to the agent tier level.';

COMMENT ON COLUMN "transaction"."special_promotions_id_fk" IS 'Reference to special promotions associated with the transaction.';

COMMENT ON COLUMN "transaction"."risk_profile_id_fk" IS 'Risk associated with financial transactions';

COMMENT ON COLUMN "transaction"."fraud_marker" IS 'Indicates whether the transaction is marked as fraudulent.';

COMMENT ON COLUMN "transaction"."fraud_eval_outcome" IS 'Outcome of fraud evaluation (e.g., Fraud, Not Fraud, Unknown).';

COMMENT ON COLUMN "transaction"."fraud_risk_score" IS 'Fraud risk score (values 1-1000).';

COMMENT ON COLUMN "transaction"."fraud_prediction_explanations" IS 'List of explanations for how each event variable impacted the fraud prediction score.';

COMMENT ON COLUMN "transaction"."fraud_rule_evaluations" IS 'Evaluations of the rules that were included in the detector version.';

COMMENT ON COLUMN "transaction"."fraud_event_num" IS 'Event number returned by AWS Fraud Detector.';

COMMENT ON COLUMN "transaction"."trans_narration" IS 'Narration containing details about the transaction.';

COMMENT ON TABLE "payment_card" IS 'We want to store as little data as possible about peoples cards.';

COMMENT ON COLUMN "payment_card"."id" IS 'Unique identifier for the payment card.';

COMMENT ON COLUMN "payment_card"."bin" IS 'Bank Identification Number (BIN) of the card.';

COMMENT ON COLUMN "payment_card"."pan" IS 'Primary Account Number (PAN) of the card.';

COMMENT ON COLUMN "payment_card"."credit_card_expired" IS 'Indicates whether the credit card has expired.';

COMMENT ON COLUMN "payment_card"."card_token" IS 'Tokenized representation of the card.';

COMMENT ON COLUMN "payment_card"."issue_number" IS 'Issue number of the card.';

COMMENT ON COLUMN "payment_card"."bill_to_city" IS 'City associated with the billing address.';

COMMENT ON COLUMN "payment_card"."masked_number" IS 'Masked version of the card number.';

COMMENT ON COLUMN "payment_card"."name" IS 'Name associated with the card.';

COMMENT ON COLUMN "payment_card"."company_name" IS 'Company name associated with the card.';

COMMENT ON COLUMN "payment_card"."card_holder_name" IS 'Name of the cardholder.';

COMMENT ON COLUMN "payment_card"."number_last_digits" IS 'Last digits of the card number.';

COMMENT ON COLUMN "payment_card"."payment_card_type" IS 'Type of payment card (e.g., Visa, Mastercard).';

COMMENT ON COLUMN "payment_card"."derived_card_type_code" IS 'Derived card type code.';

COMMENT ON COLUMN "payment_card"."expiration_year" IS 'Year of card expiration.';

COMMENT ON COLUMN "payment_card"."expiration_month" IS 'Month of card expiration.';

COMMENT ON COLUMN "payment_card"."bill_to_street" IS 'Street address associated with the billing address.';

COMMENT ON COLUMN "payment_card"."bill_to_street2" IS 'Additional street address information.';

COMMENT ON COLUMN "payment_card"."bill_to_first_name" IS 'First name associated with the billing address.';

COMMENT ON COLUMN "payment_card"."bill_to_last_name" IS 'Last name associated with the billing address.';

COMMENT ON COLUMN "payment_card"."payment_method_status" IS 'Status of the payment method.';

COMMENT ON COLUMN "payment_card"."card_number" IS 'Masked version of the card number.';

COMMENT ON COLUMN "payment_card"."cardholder_name" IS 'Name of the cardholder.';

COMMENT ON COLUMN "payment_card"."card_expiration" IS 'Expiration date of the card (stored as MM/YY format).';

COMMENT ON COLUMN "payment_card"."service_code" IS 'Service code associated with the card.';

COMMENT ON COLUMN "payment_card"."cvv" IS 'Masked or hashed version of the CVV (Card Verification Value).';

COMMENT ON TABLE "coupon" IS 'A coupon can be shared electronically and redeemed at any agent.';

COMMENT ON COLUMN "coupon"."id" IS 'Unique identifier for the coupon.';

COMMENT ON COLUMN "coupon"."value" IS 'The monetary value of the coupon.';

COMMENT ON COLUMN "coupon"."serial_no" IS 'Serial number or code associated with the coupon.';

COMMENT ON COLUMN "coupon"."active" IS 'Indicates whether the coupon is active.';

COMMENT ON COLUMN "coupon"."used" IS 'Indicates whether the coupon has been used.';

COMMENT ON COLUMN "coupon"."used_date" IS 'Date and time when the coupon was used.';

COMMENT ON COLUMN "coupon"."primary_scan_code_label" IS 'Primary scan code label associated with the coupon.';

COMMENT ON COLUMN "coupon"."is_return_coupon" IS 'Indicates whether the coupon is a return coupon.';

COMMENT ON COLUMN "coupon"."expiration_date" IS 'Date when the coupon expires.';

COMMENT ON COLUMN "coupon"."generation_date" IS 'Date and time when the coupon was generated.';

COMMENT ON COLUMN "coupon"."activation_date" IS 'Date and time when the coupon was activated.';

COMMENT ON COLUMN "coupon"."secondary_scan_code_label" IS 'Secondary scan code label associated with the coupon.';

COMMENT ON COLUMN "coupon"."scan_code_img" IS 'Image or code used for scanning the coupon.';

COMMENT ON COLUMN "coupon"."coupon_code" IS 'Code associated with the coupon.';

COMMENT ON COLUMN "coupon"."return_coupon_reason" IS 'Reason for returning the coupon.';

COMMENT ON COLUMN "coupon"."is_valid" IS 'Indicates whether the coupon is valid.';

COMMENT ON COLUMN "coupon"."coupon_status" IS 'Status of the coupon.';

COMMENT ON COLUMN "coupon"."discount_percentage" IS 'Percentage discount offered by the coupon.';

COMMENT ON COLUMN "coupon"."coupon_count" IS 'Number of coupons available.';

COMMENT ON COLUMN "coupon"."payment_method_status" IS 'Status of the payment method associated with the coupon.';

COMMENT ON TABLE "wallet" IS 'Each Point of Sale (PoS) has an individual wallet.';

COMMENT ON COLUMN "wallet"."id" IS 'Unique identifier for the wallet.';

COMMENT ON COLUMN "wallet"."agent_id_fk" IS 'Foreign key reference to the agent associated with the wallet.';

COMMENT ON COLUMN "wallet"."pos_id_fk" IS 'Foreign key reference to the Point of Sale (PoS) associated with the wallet.';

COMMENT ON COLUMN "wallet"."wallet_name" IS 'Name of the wallet.';

COMMENT ON COLUMN "wallet"."wallet_balance" IS 'The balance or amount of funds in the wallet.';

COMMENT ON COLUMN "wallet"."wallet_locked" IS 'Indicates whether the wallet is locked.';

COMMENT ON COLUMN "wallet"."wallet_active" IS 'Indicates whether the wallet is active.';

COMMENT ON COLUMN "wallet"."wallet_code" IS 'Code or identifier associated with the wallet for security purposes.';

COMMENT ON COLUMN "wallet"."wallet_crypt" IS 'Cryptographic information related to the wallet.';

COMMENT ON COLUMN "wallet"."wallet_narrative" IS 'Narrative or additional information about the wallet.';

ALTER TABLE "state" ADD FOREIGN KEY ("country_id_fk") REFERENCES "country" ("id");

ALTER TABLE "lga" ADD FOREIGN KEY ("state_id_fk") REFERENCES "state" ("id");

ALTER TABLE "ward" ADD FOREIGN KEY ("lga_id_fk") REFERENCES "lga" ("id");

ALTER TABLE "user_ext" ADD FOREIGN KEY ("manager_id_fk") REFERENCES "user_ext" ("id");

ALTER TABLE "agent" ADD FOREIGN KEY ("aggregator_id_fk") REFERENCES "agent" ("id");

ALTER TABLE "agent" ADD FOREIGN KEY ("agent_tier_id_fk") REFERENCES "agent_tier" ("id");

ALTER TABLE "agent" ADD FOREIGN KEY ("account_manager_id_fk") REFERENCES "user_ext" ("id");

ALTER TABLE "agent" ADD FOREIGN KEY ("phone_country_id_fk") REFERENCES "country" ("id");

ALTER TABLE "agent" ADD FOREIGN KEY ("alt_phone_country_id_fk") REFERENCES "country" ("id");

ALTER TABLE "agent" ADD FOREIGN KEY ("bank_id_fk") REFERENCES "bank" ("id");

ALTER TABLE "agent" ADD FOREIGN KEY ("biz_state_id_fk") REFERENCES "state" ("id");

ALTER TABLE "agent" ADD FOREIGN KEY ("biz_lga_id_fk") REFERENCES "lga" ("id");

ALTER TABLE "agent" ADD FOREIGN KEY ("registered_by_id_fk") REFERENCES "user_ext" ("id");

ALTER TABLE "agent" ADD FOREIGN KEY ("reviewed_by_id_fk") REFERENCES "user_ext" ("id");

ALTER TABLE "agent" ADD FOREIGN KEY ("approved_by_id_fk") REFERENCES "user_ext" ("id");

ALTER TABLE "agent" ADD FOREIGN KEY ("kyc_rejection_by_id_fk") REFERENCES "user_ext" ("id");

ALTER TABLE "agent" ADD FOREIGN KEY ("rejected_by_id_fk") REFERENCES "user_ext" ("id");

ALTER TABLE "contact" ADD FOREIGN KEY ("person_id_fk") REFERENCES "person" ("id");

ALTER TABLE "contact" ADD FOREIGN KEY ("agent_id_fk") REFERENCES "agent" ("id");

ALTER TABLE "contact" ADD FOREIGN KEY ("contact_type_id_fk") REFERENCES "contact_type" ("id");

ALTER TABLE "agent_person_link" ADD FOREIGN KEY ("person_id_fk") REFERENCES "person" ("id");

ALTER TABLE "agent_person_link" ADD FOREIGN KEY ("agent_id_fk") REFERENCES "agent" ("id");

ALTER TABLE "person" ADD FOREIGN KEY ("agent_id_fk") REFERENCES "agent" ("id");

ALTER TABLE "person" ADD FOREIGN KEY ("next_of_kin_id_fk") REFERENCES "person" ("id");

ALTER TABLE "person_admin_data" ADD FOREIGN KEY ("person_id_fk") REFERENCES "person" ("id");

ALTER TABLE "agent_doc_link" ADD FOREIGN KEY ("agent_id_fk") REFERENCES "agent" ("id");

ALTER TABLE "agent_doc_link" ADD FOREIGN KEY ("doc_id_fk") REFERENCES "doc" ("id");

ALTER TABLE "person_doc_link" ADD FOREIGN KEY ("person_id_fk") REFERENCES "person" ("id");

ALTER TABLE "person_doc_link" ADD FOREIGN KEY ("doc_id_fk") REFERENCES "doc" ("id");

ALTER TABLE "doc" ADD FOREIGN KEY ("doc_type_id_fk") REFERENCES "doc_type" ("id");

ALTER TABLE "doc" ADD FOREIGN KEY ("person_id_fk") REFERENCES "person" ("id");

ALTER TABLE "doc" ADD FOREIGN KEY ("agent_id_fk") REFERENCES "agent" ("id");

ALTER TABLE "doc" ADD FOREIGN KEY ("doc_content_type_id_fk") REFERENCES "mime_type" ("id");

ALTER TABLE "pos" ADD FOREIGN KEY ("return_received_by_id_fk") REFERENCES "user_ext" ("id");

ALTER TABLE "pos" ADD FOREIGN KEY ("state_id_fk") REFERENCES "state" ("id");

ALTER TABLE "pos" ADD FOREIGN KEY ("lga_id_fk") REFERENCES "lga" ("id");

ALTER TABLE "agent_pos_link" ADD FOREIGN KEY ("agent_id_fk") REFERENCES "agent" ("id");

ALTER TABLE "agent_pos_link" ADD FOREIGN KEY ("pos_id_fk") REFERENCES "pos" ("id");

ALTER TABLE "token" ADD FOREIGN KEY ("token_provider_id_fk") REFERENCES "token_provider" ("id");

ALTER TABLE "biller" ADD FOREIGN KEY ("category_id_fk") REFERENCES "biller_category" ("id");

ALTER TABLE "biller_offering" ADD FOREIGN KEY ("biller_id_fk") REFERENCES "biller" ("id");

ALTER TABLE "commission" ADD FOREIGN KEY ("agent_tier_level_id_fk") REFERENCES "agent_tier" ("id");

ALTER TABLE "commission" ADD FOREIGN KEY ("agent_id_fk") REFERENCES "agent" ("id");

ALTER TABLE "commission" ADD FOREIGN KEY ("state_id_fk") REFERENCES "state" ("id");

ALTER TABLE "commission" ADD FOREIGN KEY ("lga_id_fk") REFERENCES "lga" ("id");

ALTER TABLE "commission" ADD FOREIGN KEY ("currency_id_fk") REFERENCES "currency" ("id");

ALTER TABLE "commission" ADD FOREIGN KEY ("risk_profile_id_fk") REFERENCES "risk_profile" ("id");

ALTER TABLE "commission" ADD FOREIGN KEY ("biller_id_fk") REFERENCES "biller" ("id");

ALTER TABLE "commission" ADD FOREIGN KEY ("biller_offering_id_fk") REFERENCES "biller_offering" ("id");

ALTER TABLE "commission" ADD FOREIGN KEY ("transaction_type_id_fk") REFERENCES "trans_type" ("id");

ALTER TABLE "commission" ADD FOREIGN KEY ("customer_segment_id_fk") REFERENCES "customer_segment" ("id");

ALTER TABLE "commission" ADD FOREIGN KEY ("special_promotion_id_fk") REFERENCES "promotion" ("id");

ALTER TABLE "transaction" ADD FOREIGN KEY ("coupon_id_fk") REFERENCES "coupon" ("id");

ALTER TABLE "transaction" ADD FOREIGN KEY ("agent_id_fk") REFERENCES "agent" ("id");

ALTER TABLE "transaction" ADD FOREIGN KEY ("payment_card_id_fk") REFERENCES "payment_card" ("id");

ALTER TABLE "transaction" ADD FOREIGN KEY ("pos_id_fk") REFERENCES "pos" ("id");

ALTER TABLE "transaction" ADD FOREIGN KEY ("wallet_id_fk") REFERENCES "wallet" ("id");

ALTER TABLE "transaction" ADD FOREIGN KEY ("biller_id_fk") REFERENCES "biller" ("id");

ALTER TABLE "transaction" ADD FOREIGN KEY ("biller_offering_id_fk") REFERENCES "biller_offering" ("id");

ALTER TABLE "transaction" ADD FOREIGN KEY ("currency_id_fk") REFERENCES "currency" ("id");

ALTER TABLE "transaction" ADD FOREIGN KEY ("trans_route_id_fk") REFERENCES "trans_routing_threshold" ("id");

ALTER TABLE "transaction" ADD FOREIGN KEY ("origin_bank_id_fk") REFERENCES "bank" ("id");

ALTER TABLE "transaction" ADD FOREIGN KEY ("bene_bank_id_fk") REFERENCES "bank" ("id");

ALTER TABLE "transaction" ADD FOREIGN KEY ("customer_segment_id_fk") REFERENCES "customer_segment" ("id");

ALTER TABLE "transaction" ADD FOREIGN KEY ("agent_tier_level_id_fk") REFERENCES "agent_tier" ("id");

ALTER TABLE "transaction" ADD FOREIGN KEY ("special_promotions_id_fk") REFERENCES "promotion" ("id");

ALTER TABLE "transaction" ADD FOREIGN KEY ("risk_profile_id_fk") REFERENCES "risk_profile" ("id");

ALTER TABLE "wallet" ADD FOREIGN KEY ("agent_id_fk") REFERENCES "agent" ("id");

ALTER TABLE "wallet" ADD FOREIGN KEY ("pos_id_fk") REFERENCES "pos" ("id");
