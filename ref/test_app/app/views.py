from flask_appbuilder import ModelView
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder.views import MasterDetailView, MultipleView
from .models import *

class Tech_parametersView(ModelView):
    datamodel = SQLAInterface(Tech_parameters)
    list_columns = ['key', 'value', 'enabled', 'notes']

class Ab_permissionView(ModelView):
    datamodel = SQLAInterface(Ab_permission)
    list_columns = ['name']

class Ab_register_userView(ModelView):
    datamodel = SQLAInterface(Ab_register_user)
    list_columns = ['first_name', 'last_name', 'username', 'password', 'email', 'registration_date', 'registration_hash']

class Ab_roleView(ModelView):
    datamodel = SQLAInterface(Ab_role)
    list_columns = ['name']

class Ab_userView(ModelView):
    datamodel = SQLAInterface(Ab_user)
    list_columns = ['first_name', 'last_name', 'username', 'password', 'active', 'email', 'last_login', 'login_count', 'fail_login_count', 'created_on', 'changed_on', 'created_by_fk', 'changed_by_fk']

class Ab_view_menuView(ModelView):
    datamodel = SQLAInterface(Ab_view_menu)
    list_columns = ['name']

class Agent_tierView(ModelView):
    datamodel = SQLAInterface(Agent_tier)
    list_columns = ['name', 'notes']

class BankView(ModelView):
    datamodel = SQLAInterface(Bank)
    list_columns = ['code', 'name', 'category', 'swift_code', 'sort_code', 'iban', 'cust_care_phone', 'cust_care_email', 'escalation_contact', 'created_on', 'updated_on']

class Biller_categoryView(ModelView):
    datamodel = SQLAInterface(Biller_category)
    list_columns = ['biller_cat_id', 'biller_cat_name', 'biller_cat_notes']

class Contact_typeView(ModelView):
    datamodel = SQLAInterface(Contact_type)
    list_columns = ['name', 'description', 'is_digital', 'requires_verification', 'max_length', 'icon_url', 'created_at', 'updated_at']

class CountryView(ModelView):
    datamodel = SQLAInterface(Country)
    list_columns = ['name', 'code', 'phone_code']

class CouponView(ModelView):
    datamodel = SQLAInterface(Coupon)
    list_columns = ['coupon_id', 'coupon_value', 'active', 'used', 'used_date', 'primary_scan_code_label', 'is_return_coupon', 'expiration_date', 'generation_date', 'activation_date', 'secondary_scan_code_label', 'scan_code_img', 'coupon_code', 'return_coupon_reason', 'is_valid', 'coupon_status', 'discount_percentage', 'coupon_count', 'payment_method_status']

class CurrencyView(ModelView):
    datamodel = SQLAInterface(Currency)
    list_columns = ['name', 'symbol', 'numeric_code', 'full_name', 'decimal_places', 'internationalized_name_code']

class Customer_segmentView(ModelView):
    datamodel = SQLAInterface(Customer_segment)
    list_columns = ['cs_id', 'cs_name', 'cs_notes']

class Doc_typeView(ModelView):
    datamodel = SQLAInterface(Doc_type)
    list_columns = ['name', 'doc_category', 'notes', 'required_information', 'is_serialized', 'serial_length', 'expires', 'validity_period', 'renewal_frequency', 'is_government_issued', 'is_digital', 'template_url', 'example_image_url', 'created_at', 'updated_at']

class Mime_typeView(ModelView):
    datamodel = SQLAInterface(Mime_type)
    list_columns = ['label', 'mime_type', 'file_extension']

class Mime_type_mapView(ModelView):
    datamodel = SQLAInterface(Mime_type_map)
    list_columns = ['extension', 'mime_type']

class Payment_cardView(ModelView):
    datamodel = SQLAInterface(Payment_card)
    list_columns = ['bin', 'pan', 'credit_card_expired', 'card_token', 'issue_number', 'bill_to_city', 'masked_number', 'name', 'company_name', 'card_holder_name', 'number_last_digits', 'payment_card_type', 'derived_card_type_code', 'expiration_year', 'expiration_month', 'bill_to_street', 'bill_to_street2', 'bill_to_first_name', 'bill_to_last_name', 'payment_method_status', 'card_number', 'cardholder_name', 'card_expiration', 'service_code', 'cvv']

class PromotionView(ModelView):
    datamodel = SQLAInterface(Promotion)
    list_columns = ['promo_id', 'promo_name', 'promo_notes', 'promo_start_date', 'promo_end_date']

class Token_providerView(ModelView):
    datamodel = SQLAInterface(Token_provider)
    list_columns = ['token_provider_id', 'token_provider_name', 'token_provioder_notes', 'token_provider_priv_key', 'token_provider_pub_key', 'token_provider_endpoint', 'token_provider_protocol', 'token_provider_auth', 'token_provider_ssl', 'token_provider_ip_whitelist', 'token_provider_password', 'enabled']

class Trans_routing_thresholdsView(ModelView):
    datamodel = SQLAInterface(Trans_routing_thresholds)
    list_columns = ['trans_route_id', 'trans_route_name', 'trans_route_min', 'trans_route_max', 'trans_route_priority']

class Trans_typeView(ModelView):
    datamodel = SQLAInterface(Trans_type)
    list_columns = ['tt_id', 'tt_name', 'tt_notes']

class User_extView(ModelView):
    datamodel = SQLAInterface(User_ext)
    list_columns = [manager, 'first_name', 'middle_name', 'surname', 'employee_number', 'job_title', 'phone_number', 'email', 'user_data']

class Ab_permission_viewView(ModelView):
    datamodel = SQLAInterface(Ab_permission_view)
    list_columns = ['permission_id', 'view_menu_id']

class Ab_user_roleView(ModelView):
    datamodel = SQLAInterface(Ab_user_role)
    list_columns = ['user_id', 'role_id']

class BillerView(ModelView):
    datamodel = SQLAInterface(Biller)
    list_columns = ['biller_id', biller_cat, 'biller_code', 'biller_name', 'biller_url', 'biller_note']

class StateView(ModelView):
    datamodel = SQLAInterface(State)
    list_columns = [country, 'state_code', 'state_name', 'state_desc']

class TokenView(ModelView):
    datamodel = SQLAInterface(Token)
    list_columns = ['token_id', token_provider, 'token_name', 'token_issue_date', 'token_expiry_date', 'token_validity', 'token_expired', 'token_value', 'token_username', 'token_password', 'token_notes', 'token_client_secret', 'enabled']

class Ab_permission_view_roleView(ModelView):
    datamodel = SQLAInterface(Ab_permission_view_role)
    list_columns = ['permission_view_id', 'role_id']

class Biller_offeringView(ModelView):
    datamodel = SQLAInterface(Biller_offering)
    list_columns = [biller, 'biller_offering_id', 'offering_name', 'offering_description', 'offering_price']

class LgaView(ModelView):
    datamodel = SQLAInterface(Lga)
    list_columns = [state, 'code', 'lga_name']

class AgentView(ModelView):
    datamodel = SQLAInterface(Agent)
    list_columns = [aggregator, 'is_aggregator', 'became_aggregator_date', 'assigned_pos_count', 'aggregator_pos_threshold', 'registration_status', 'registration_status_notes', 'agent_type', 'agent_role', agent_tier, account_manager, 'agent_name', 'alias', phone_country, 'phone', 'phone_ext', alt_phone_country, 'alt_phone', 'alt_phone_ext', 'email', 'alt_email', 'bvn', 'bvn_verified', 'bvn_verification_date', 'bvn_verification_code', 'tax_id', bank, 'bank_acc_no', 'biz_name', biz_state, biz_lga, 'biz_city', 'biz_city_area', 'biz_street', 'biz_building', 'biz_address', 'biz_poa_img', 'biz_poa_desc', 'biz_poa_valid', 'biz_lat', 'biz_lon', 'biz_loc', 'biz_ggl_code', 'company_name', 'cac_number', 'cac_reg_date', 'cac_cert_img', 'cac_cert_no', 'ref_code', 'access_pin', 'registered_by_fk', 'registration_date', 'reviewed_by_fk', 'review_date', 'approved_by_fk', 'approval_date', 'approval_narrative', 'kyc_submit_date', 'kyc_verification_status', 'kyc_approval_date', 'kyc_ref_code', 'kyc_rejection_narrative', 'kyc_rejection_by_fk', 'rejection_date', 'rejection_narrative', 'rejected_by_fk', 'face_matrix', 'finger_print_img', 'agent_public_key', 'agent_pj_expiry', 'agent_history']

class PosView(ModelView):
    datamodel = SQLAInterface(Pos)
    list_columns = ['serial_no', 'imei', 'mac_addr', 'device_model', 'device_make', 'device_mfg', 'os_version', 'device_color', 'device_condition', 'status', 'owner_type', 'registration_date', 'assigned', 'assigned_date', 'assigned_narrative', 'active', 'activation_date', 'last_active', 'deployed', 'deploy_date', 'deploy_narrative', 'returned', 'return_date', 'return_narrative', 'return_received_date', 'return_received_by', 'state_id', 'lga_id', 'street_address', 'building_name', 'contact_phone_num', 'pos_user', 'crypt_priv_key', 'crypt_pub_key', 'crypt_password', 'override_key']

class Agent_pos_linkView(ModelView):
    datamodel = SQLAInterface(Agent_pos_link)
    list_columns = [agent, pos, 'assigned_date', 'assigned_by', 'received_by', 'received_date', 'received_location', 'delivery_note', 'delivery_note_printed', 'activated', 'activation_date', 'activation_otp', 'otp_sent', 'otp_sent_time', 'otp_used', 'history']

class Comm_refView(ModelView):
    datamodel = SQLAInterface(Comm_ref)
    list_columns = ['cr_id', 'agent_type', 'agent_tier_level', agent, state, lga, biller, biller_offering, transaction_type, customer_segment, special_promotion, 'min_trans_amount', 'max_trans_amount', 'min_max_step', 'min_comm_amount', 'max_comm_amount', 'commission_rate', 'start_time', 'end_time', 'start_date', 'end_date']

class PersonView(ModelView):
    datamodel = SQLAInterface(Person)
    list_columns = [agent, next_of_kin, 'person_role', 'first_name', 'middle_name', 'surname', 'nick_name', 'gender', 'photo_img', 'signature_img', 'bvn_no', 'bvn_verified', 'bvn_verification_date', 'bvn_verification_code', 'tax_id', 'home_poa_img', 'home_poa_desc', 'home_poa_valid', 'home_lat', 'home_lon', 'home_loc', 'home_ggl_code']

class WalletView(ModelView):
    datamodel = SQLAInterface(Wallet)
    list_columns = ['wallet_id', agent, pos, 'wallet_name', 'wallet_balance', 'wallet_locked', 'wallet_active', 'wallet_code', 'wallet_crypt', 'wallet_narrative']

class Agent_person_linkView(ModelView):
    datamodel = SQLAInterface(Agent_person_link)
    list_columns = [person, agent]

class ContactView(ModelView):
    datamodel = SQLAInterface(Contact)
    list_columns = [person, agent, contact_type, 'contact', 'priority', 'best_time_to_contact_start', 'best_time_to_contact_end', 'active_from_date', 'active_to_date', 'for_business_use', 'for_personal_use', 'do_not_use', 'is_active', 'is_blocked', 'is_verified', 'notes']

class DocView(ModelView):
    datamodel = SQLAInterface(Doc)
    list_columns = [doc_type, person, agent, 'doc_name', 'doc_content_type', 'doc_binaary', 'doc_url', 'doc_length', 'doc_text', 'identification_number', 'serial_number', 'description', 'file_name', 'page_count', 'issued_on', 'issued_by_authority', 'issued_at', 'expires_on', 'expired', 'verified', 'verification_date', 'verification_code', 'uploaded_on', 'updated_on']

class Person_additional_dataView(ModelView):
    datamodel = SQLAInterface(Person_additional_data)
    list_columns = [person, 'Gender', 'religion', 'ethnicity', 'consumer_credit_score', 'is_home_owner', 'person_height', 'person_weight', 'person_height_unit_of_measure', 'person_weight_unit_of_measure', 'highest_education_level', 'person_life_stage', 'mothers_maiden_name', 'Marital_Status_cd', 'citizenship_fk', 'From_whom', 'Amount', 'Interest_rate_pa', 'Number_of_people_depending_on_overal_income', 'YesNo_cd_Bank_account', 'YesNo_cd_Business_plan_provided', 'YesNo_cd_Access_to_internet', 'Introduced_by', 'Known_to_introducer_since', 'Last_visited_by', 'Last_visited_on']

class Person_admin_dataView(ModelView):
    datamodel = SQLAInterface(Person_admin_data)
    list_columns = [person, 'creation_time', 'failed_login_count', 'failed_login_timestamp', 'password_last_set_time', 'profile_picture', 'awatar', 'screen_name', 'user_priv_cert', 'user_pub_cert', 'alt_security_identities', 'generated_UID', 'do_not_email', 'do_not_phone', 'do_not_mail', 'do_not_sms', 'do_not_trade', 'opted_out', 'do_not_track_update_date', 'do_not_process_from_update_date', 'do_not_market_from_update_date', 'do_not_track_location_update_date', 'do_not_profile_from_update_date', 'do_forget_me_from_update_date', 'do_not_process_reason', 'no_merge_reason', 'do_extract_my_data_update_date', 'should_forget', 'consumer_credit_score_provider_name', 'web_site_url', 'ordering_name', 'hospitalizations_last5_years_count', 'surgeries_last5_years_count', 'dependent_count', 'account_locked', 'send_individual_data', 'influencer_rating']

class TransView(ModelView):
    datamodel = SQLAInterface(Trans)
    list_columns = ['trans_id', coupon, 'customer_name', 'trans_purpose', 'customer_id', 'transaction_type', 'card_trans_type', agent, payment_card, pos, wallet, biller, biller_offering, 'trans_time', currency, 'trans_status', trans_route, 'origin_source', 'origin_ref_code', 'origin_trans_notes', origin_bank, 'origin_institution_code', 'origin_account_num', 'origin_account_name', 'origin_KYC_Level', 'origin_Bank_Verification_Number', 'origin_bvn', 'session_ref', 'transaction_ref', 'channelCode', 'name_enquiry_ref', 'api_transactionid', 'receipt_no', 'pin_based', 'pin_code', 'pin_option', 'authorization_code', 'acquirer_name', 'currency', 'transaction_location', 'payment_reference', 'response_code', 'trans_dest', 'bene_ref_code', 'bene_trans_notes', bene_bank, 'bene_account_num', 'bene_institution_code', 'bene_bank_verification_number', 'bene_KYC_Level', 'bene_account_name', 'bene_phone_number', 'bene_phone_denom', 'bene_phone_product', 'transaction_amount', 'available_balance', 'svc_fees', 'comm_total', 'comm_agent', 'comm_aggr', 'comm_ours', 'comm_other', 'comm_net_pct', 'tax', 'excise_duty', 'vat', 'transmit_amount', 'comm_narration', 'trans_currency', 'trans_convert_currency', 'trans_currency_exchange_rate', 'trans_date', customer_segment, agent_tier_level, special_promotions, 'fraud_marker', 'fraud_eval_outcome', 'fraud_risk_score', 'fraud_prediction_explanations', 'fraud_rule_evaluations', 'fraud_event_num', 'trans_narration']

class Agent_doc_linkView(ModelView):
    datamodel = SQLAInterface(Agent_doc_link)
    list_columns = [agent, doc, 'verification_status', 'submit_date', 'notes']

class Person_doc_linkView(ModelView):
    datamodel = SQLAInterface(Person_doc_link)
    list_columns = [person, doc, 'verification_status', 'submit_date']

class Ab_userAb_userMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Ab_user)
    related_views = [Ab_userView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class Ab_userAb_userMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Ab_user)
    related_views = [Ab_userView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class User_extUser_extMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(User_ext)
    related_views = [User_extView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class Ab_view_menuAb_permission_viewMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Ab_view_menu)
    related_views = [Ab_permission_viewView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class Ab_permissionAb_permission_viewMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Ab_permission)
    related_views = [Ab_permission_viewView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class Ab_roleAb_user_roleMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Ab_role)
    related_views = [Ab_user_roleView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class Ab_userAb_user_roleMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Ab_user)
    related_views = [Ab_user_roleView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class Biller_categoryBillerMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Biller_category)
    related_views = [BillerView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class CountryStateMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Country)
    related_views = [StateView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class Token_providerTokenMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Token_provider)
    related_views = [TokenView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class Ab_permission_viewAb_permission_view_roleMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Ab_permission_view)
    related_views = [Ab_permission_view_roleView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class Ab_roleAb_permission_view_roleMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Ab_role)
    related_views = [Ab_permission_view_roleView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class BillerBiller_offeringMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Biller)
    related_views = [Biller_offeringView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class StateLgaMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(State)
    related_views = [LgaView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class StateAgentMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(State)
    related_views = [AgentView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class User_extAgentMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(User_ext)
    related_views = [AgentView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class LgaAgentMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Lga)
    related_views = [AgentView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class CountryAgentMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Country)
    related_views = [AgentView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class User_extAgentMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(User_ext)
    related_views = [AgentView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class Agent_tierAgentMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Agent_tier)
    related_views = [AgentView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class User_extAgentMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(User_ext)
    related_views = [AgentView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class User_extAgentMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(User_ext)
    related_views = [AgentView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class User_extAgentMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(User_ext)
    related_views = [AgentView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class BankAgentMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Bank)
    related_views = [AgentView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class AgentAgentMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Agent)
    related_views = [AgentView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class CountryAgentMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Country)
    related_views = [AgentView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class User_extAgentMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(User_ext)
    related_views = [AgentView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class StatePosMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(State)
    related_views = [PosView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class LgaPosMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Lga)
    related_views = [PosView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class User_extPosMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(User_ext)
    related_views = [PosView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class PosAgent_pos_linkMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Pos)
    related_views = [Agent_pos_linkView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class AgentAgent_pos_linkMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Agent)
    related_views = [Agent_pos_linkView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class Agent_tierComm_refMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Agent_tier)
    related_views = [Comm_refView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class Biller_offeringComm_refMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Biller_offering)
    related_views = [Comm_refView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class Customer_segmentComm_refMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Customer_segment)
    related_views = [Comm_refView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class StateComm_refMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(State)
    related_views = [Comm_refView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class Trans_typeComm_refMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Trans_type)
    related_views = [Comm_refView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class LgaComm_refMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Lga)
    related_views = [Comm_refView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class PromotionComm_refMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Promotion)
    related_views = [Comm_refView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class AgentComm_refMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Agent)
    related_views = [Comm_refView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class BillerComm_refMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Biller)
    related_views = [Comm_refView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class AgentPersonMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Agent)
    related_views = [PersonView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class PersonPersonMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Person)
    related_views = [PersonView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class AgentWalletMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Agent)
    related_views = [WalletView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class PosWalletMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Pos)
    related_views = [WalletView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class PersonAgent_person_linkMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Person)
    related_views = [Agent_person_linkView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class AgentAgent_person_linkMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Agent)
    related_views = [Agent_person_linkView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class Contact_typeContactMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Contact_type)
    related_views = [ContactView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class PersonContactMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Person)
    related_views = [ContactView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class AgentContactMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Agent)
    related_views = [ContactView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class Mime_typeDocMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Mime_type)
    related_views = [DocView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class AgentDocMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Agent)
    related_views = [DocView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class PersonDocMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Person)
    related_views = [DocView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class Doc_typeDocMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Doc_type)
    related_views = [DocView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class PersonPerson_additional_dataMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Person)
    related_views = [Person_additional_dataView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class CountryPerson_additional_dataMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Country)
    related_views = [Person_additional_dataView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class PersonPerson_admin_dataMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Person)
    related_views = [Person_admin_dataView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class Biller_offeringTransMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Biller_offering)
    related_views = [TransView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class Customer_segmentTransMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Customer_segment)
    related_views = [TransView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class BankTransMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Bank)
    related_views = [TransView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class PosTransMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Pos)
    related_views = [TransView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class BillerTransMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Biller)
    related_views = [TransView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class CurrencyTransMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Currency)
    related_views = [TransView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class PromotionTransMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Promotion)
    related_views = [TransView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class Agent_tierTransMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Agent_tier)
    related_views = [TransView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class BankTransMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Bank)
    related_views = [TransView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class Payment_cardTransMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Payment_card)
    related_views = [TransView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class WalletTransMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Wallet)
    related_views = [TransView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class CouponTransMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Coupon)
    related_views = [TransView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class AgentTransMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Agent)
    related_views = [TransView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class Trans_routing_thresholdsTransMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Trans_routing_thresholds)
    related_views = [TransView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class DocAgent_doc_linkMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Doc)
    related_views = [Agent_doc_linkView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class AgentAgent_doc_linkMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Agent)
    related_views = [Agent_doc_linkView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class DocPerson_doc_linkMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Doc)
    related_views = [Person_doc_linkView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class PersonPerson_doc_linkMasterDetailView(MasterDetailView):
    datamodel = SQLAInterface(Person)
    related_views = [Person_doc_linkView]
    show_template = 'appbuilder/general/model/show_cascade.html'

class Ab_permissionMultipleView(MultipleView):
    datamodel = SQLAInterface(Ab_permission)
    views = [Ab_view_menuView, Ab_permissionView]

class Ab_userMultipleView(MultipleView):
    datamodel = SQLAInterface(Ab_user)
    views = [Ab_userView, Ab_roleView]

class Ab_roleMultipleView(MultipleView):
    datamodel = SQLAInterface(Ab_role)
    views = [Ab_permission_viewView, Ab_roleView]

class User_extMultipleView(MultipleView):
    datamodel = SQLAInterface(User_ext)
    views = [BankView, AgentView, Agent_tierView, LgaView, User_extView, StateView, CountryView]

class User_extMultipleView(MultipleView):
    datamodel = SQLAInterface(User_ext)
    views = [StateView, LgaView, User_extView]

class AgentMultipleView(MultipleView):
    datamodel = SQLAInterface(Agent)
    views = [PosView, AgentView]

class BillerMultipleView(MultipleView):
    datamodel = SQLAInterface(Biller)
    views = [BillerView, AgentView, Agent_tierView, LgaView, Biller_offeringView, PromotionView, Trans_typeView, Customer_segmentView, StateView]

class PersonMultipleView(MultipleView):
    datamodel = SQLAInterface(Person)
    views = [PersonView, AgentView]

class PosMultipleView(MultipleView):
    datamodel = SQLAInterface(Pos)
    views = [PosView, AgentView]

class AgentMultipleView(MultipleView):
    datamodel = SQLAInterface(Agent)
    views = [PersonView, AgentView]

class AgentMultipleView(MultipleView):
    datamodel = SQLAInterface(Agent)
    views = [Contact_typeView, PersonView, AgentView]

class Doc_typeMultipleView(MultipleView):
    datamodel = SQLAInterface(Doc_type)
    views = [Doc_typeView, PersonView, Mime_typeView, AgentView]

class CountryMultipleView(MultipleView):
    datamodel = SQLAInterface(Country)
    views = [PersonView, CountryView]

class Trans_routing_thresholdsMultipleView(MultipleView):
    datamodel = SQLAInterface(Trans_routing_thresholds)
    views = [BillerView, CurrencyView, AgentView, CouponView, Agent_tierView, PosView, Biller_offeringView, PromotionView, Trans_routing_thresholdsView, Customer_segmentView, BankView, WalletView, Payment_cardView]

class AgentMultipleView(MultipleView):
    datamodel = SQLAInterface(Agent)
    views = [DocView, AgentView]

class PersonMultipleView(MultipleView):
    datamodel = SQLAInterface(Person)
    views = [PersonView, DocView]

appbuilder.add_view(Tech_parametersView, "Tech_parameterss", icon="fa-folder-open-o", category="Setup")
appbuilder.add_view(Ab_permissionView, "Ab_permissions", icon="fa-folder-open-o", category="Setup")
appbuilder.add_view(Ab_register_userView, "Ab_register_users", icon="fa-folder-open-o", category="Setup")
appbuilder.add_view(Ab_roleView, "Ab_roles", icon="fa-folder-open-o", category="Setup")
appbuilder.add_view(Ab_userView, "Ab_users", icon="fa-folder-open-o", category="Setup")
appbuilder.add_view(Ab_view_menuView, "Ab_view_menus", icon="fa-folder-open-o", category="Setup")
appbuilder.add_view(Agent_tierView, "Agent_tiers", icon="fa-folder-open-o", category="Setup")
appbuilder.add_view(BankView, "Banks", icon="fa-folder-open-o", category="Setup")
appbuilder.add_view(Biller_categoryView, "Biller_categorys", icon="fa-folder-open-o", category="Setup")
appbuilder.add_view(Contact_typeView, "Contact_types", icon="fa-folder-open-o", category="Setup")
appbuilder.add_view(CountryView, "Countrys", icon="fa-folder-open-o", category="Setup")
appbuilder.add_view(CouponView, "Coupons", icon="fa-folder-open-o", category="Setup")
appbuilder.add_view(CurrencyView, "Currencys", icon="fa-folder-open-o", category="Setup")
appbuilder.add_view(Customer_segmentView, "Customer_segments", icon="fa-folder-open-o", category="Setup")
appbuilder.add_view(Doc_typeView, "Doc_types", icon="fa-folder-open-o", category="Setup")
appbuilder.add_view(Mime_typeView, "Mime_types", icon="fa-folder-open-o", category="Setup")
appbuilder.add_view(Mime_type_mapView, "Mime_type_maps", icon="fa-folder-open-o", category="Setup")
appbuilder.add_view(Payment_cardView, "Payment_cards", icon="fa-folder-open-o", category="Setup")
appbuilder.add_view(PromotionView, "Promotions", icon="fa-folder-open-o", category="Setup")
appbuilder.add_view(Token_providerView, "Token_providers", icon="fa-folder-open-o", category="Setup")
appbuilder.add_view(Trans_routing_thresholdsView, "Trans_routing_thresholdss", icon="fa-folder-open-o", category="Setup")
appbuilder.add_view(Trans_typeView, "Trans_types", icon="fa-folder-open-o", category="Setup")
appbuilder.add_view(User_extView, "User_exts", icon="fa-folder-open-o", category="Setup")
appbuilder.add_view(Ab_permission_viewView, "Ab_permission_views", icon="fa-folder-open-o", category="Setup")
appbuilder.add_view(Ab_user_roleView, "Ab_user_roles", icon="fa-folder-open-o", category="Setup")
appbuilder.add_view(BillerView, "Billers", icon="fa-folder-open-o", category="Setup")
appbuilder.add_view(StateView, "States", icon="fa-folder-open-o", category="Setup")
appbuilder.add_view(TokenView, "Tokens", icon="fa-folder-open-o", category="Setup")
appbuilder.add_view(Ab_permission_view_roleView, "Ab_permission_view_roles", icon="fa-folder-open-o", category="Setup")
appbuilder.add_view(Biller_offeringView, "Biller_offerings", icon="fa-folder-open-o", category="Setup")
appbuilder.add_view(LgaView, "Lgas", icon="fa-folder-open-o", category="Setup")
appbuilder.add_view(AgentView, "Agents", icon="fa-folder-open-o", category="Setup")
appbuilder.add_view(PosView, "Poss", icon="fa-folder-open-o", category="Setup")
appbuilder.add_view(Agent_pos_linkView, "Agent_pos_links", icon="fa-folder-open-o", category="Setup")
appbuilder.add_view(Comm_refView, "Comm_refs", icon="fa-folder-open-o", category="Setup")
appbuilder.add_view(PersonView, "People", icon="fa-folder-open-o", category="Setup")
appbuilder.add_view(WalletView, "Wallets", icon="fa-folder-open-o", category="Setup")
appbuilder.add_view(Agent_person_linkView, "Agent_person_links", icon="fa-folder-open-o", category="Setup")
appbuilder.add_view(ContactView, "Contacts", icon="fa-folder-open-o", category="Setup")
appbuilder.add_view(DocView, "Docs", icon="fa-folder-open-o", category="Setup")
appbuilder.add_view(Person_additional_dataView, "Person_additional_datas", icon="fa-folder-open-o", category="Setup")
appbuilder.add_view(Person_admin_dataView, "Person_admin_datas", icon="fa-folder-open-o", category="Setup")
appbuilder.add_view(TransView, "Transs", icon="fa-folder-open-o", category="Setup")
appbuilder.add_view(Agent_doc_linkView, "Agent_doc_links", icon="fa-folder-open-o", category="Setup")
appbuilder.add_view(Person_doc_linkView, "Person_doc_links", icon="fa-folder-open-o", category="Setup")
appbuilder.add_view(Ab_userAb_userMasterDetailView, "Ab_users", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(Ab_userAb_userMasterDetailView, "Ab_users", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(User_extUser_extMasterDetailView, "User_exts", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(Ab_view_menuAb_permission_viewMasterDetailView, "Ab_view_menus", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(Ab_permissionAb_permission_viewMasterDetailView, "Ab_permissions", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(Ab_roleAb_user_roleMasterDetailView, "Ab_roles", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(Ab_userAb_user_roleMasterDetailView, "Ab_users", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(Biller_categoryBillerMasterDetailView, "Biller_categorys", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(CountryStateMasterDetailView, "Countrys", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(Token_providerTokenMasterDetailView, "Token_providers", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(Ab_permission_viewAb_permission_view_roleMasterDetailView, "Ab_permission_views", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(Ab_roleAb_permission_view_roleMasterDetailView, "Ab_roles", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(BillerBiller_offeringMasterDetailView, "Billers", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(StateLgaMasterDetailView, "States", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(StateAgentMasterDetailView, "States", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(User_extAgentMasterDetailView, "User_exts", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(LgaAgentMasterDetailView, "Lgas", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(CountryAgentMasterDetailView, "Countrys", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(User_extAgentMasterDetailView, "User_exts", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(Agent_tierAgentMasterDetailView, "Agent_tiers", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(User_extAgentMasterDetailView, "User_exts", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(User_extAgentMasterDetailView, "User_exts", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(User_extAgentMasterDetailView, "User_exts", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(BankAgentMasterDetailView, "Banks", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(AgentAgentMasterDetailView, "Agents", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(CountryAgentMasterDetailView, "Countrys", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(User_extAgentMasterDetailView, "User_exts", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(StatePosMasterDetailView, "States", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(LgaPosMasterDetailView, "Lgas", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(User_extPosMasterDetailView, "User_exts", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(PosAgent_pos_linkMasterDetailView, "Poss", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(AgentAgent_pos_linkMasterDetailView, "Agents", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(Agent_tierComm_refMasterDetailView, "Agent_tiers", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(Biller_offeringComm_refMasterDetailView, "Biller_offerings", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(Customer_segmentComm_refMasterDetailView, "Customer_segments", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(StateComm_refMasterDetailView, "States", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(Trans_typeComm_refMasterDetailView, "Trans_types", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(LgaComm_refMasterDetailView, "Lgas", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(PromotionComm_refMasterDetailView, "Promotions", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(AgentComm_refMasterDetailView, "Agents", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(BillerComm_refMasterDetailView, "Billers", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(AgentPersonMasterDetailView, "Agents", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(PersonPersonMasterDetailView, "People", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(AgentWalletMasterDetailView, "Agents", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(PosWalletMasterDetailView, "Poss", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(PersonAgent_person_linkMasterDetailView, "People", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(AgentAgent_person_linkMasterDetailView, "Agents", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(Contact_typeContactMasterDetailView, "Contact_types", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(PersonContactMasterDetailView, "People", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(AgentContactMasterDetailView, "Agents", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(Mime_typeDocMasterDetailView, "Mime_types", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(AgentDocMasterDetailView, "Agents", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(PersonDocMasterDetailView, "People", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(Doc_typeDocMasterDetailView, "Doc_types", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(PersonPerson_additional_dataMasterDetailView, "People", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(CountryPerson_additional_dataMasterDetailView, "Countrys", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(PersonPerson_admin_dataMasterDetailView, "People", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(Biller_offeringTransMasterDetailView, "Biller_offerings", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(Customer_segmentTransMasterDetailView, "Customer_segments", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(BankTransMasterDetailView, "Banks", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(PosTransMasterDetailView, "Poss", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(BillerTransMasterDetailView, "Billers", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(CurrencyTransMasterDetailView, "Currencys", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(PromotionTransMasterDetailView, "Promotions", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(Agent_tierTransMasterDetailView, "Agent_tiers", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(BankTransMasterDetailView, "Banks", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(Payment_cardTransMasterDetailView, "Payment_cards", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(WalletTransMasterDetailView, "Wallets", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(CouponTransMasterDetailView, "Coupons", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(AgentTransMasterDetailView, "Agents", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(Trans_routing_thresholdsTransMasterDetailView, "Trans_routing_thresholdss", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(DocAgent_doc_linkMasterDetailView, "Docs", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(AgentAgent_doc_linkMasterDetailView, "Agents", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(DocPerson_doc_linkMasterDetailView, "Docs", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(PersonPerson_doc_linkMasterDetailView, "People", icon="fa-folder-open-o", category="Review")
appbuilder.add_view(Ab_permission, "Ab_permissions", icon="fa-folder-open-o", category="Inspect")
appbuilder.add_view(Ab_user, "Ab_users", icon="fa-folder-open-o", category="Inspect")
appbuilder.add_view(Ab_role, "Ab_roles", icon="fa-folder-open-o", category="Inspect")
appbuilder.add_view(User_ext, "User_exts", icon="fa-folder-open-o", category="Inspect")
appbuilder.add_view(User_ext, "User_exts", icon="fa-folder-open-o", category="Inspect")
appbuilder.add_view(Agent, "Agents", icon="fa-folder-open-o", category="Inspect")
appbuilder.add_view(Biller, "Billers", icon="fa-folder-open-o", category="Inspect")
appbuilder.add_view(Person, "People", icon="fa-folder-open-o", category="Inspect")
appbuilder.add_view(Pos, "Poss", icon="fa-folder-open-o", category="Inspect")
appbuilder.add_view(Agent, "Agents", icon="fa-folder-open-o", category="Inspect")
appbuilder.add_view(Agent, "Agents", icon="fa-folder-open-o", category="Inspect")
appbuilder.add_view(Doc_type, "Doc_types", icon="fa-folder-open-o", category="Inspect")
appbuilder.add_view(Country, "Countrys", icon="fa-folder-open-o", category="Inspect")
appbuilder.add_view(Trans_routing_thresholds, "Trans_routing_thresholdss", icon="fa-folder-open-o", category="Inspect")
appbuilder.add_view(Agent, "Agents", icon="fa-folder-open-o", category="Inspect")
appbuilder.add_view(Person, "People", icon="fa-folder-open-o", category="Inspect")