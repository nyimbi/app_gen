from flask_appbuilder.api import ModelRestApi, BaseApi, expose, rison
from flask_appbuilder.models.sqla.interface import SQLAInterface
class Tech_parametersApi(ModelRestApi):
    resource_name = "Tech_Parameters"
    datamodel = SQLAInterface(Tech_parameters)

appbuilder.add_api(Tech_parametersApi)

class Ab_permissionApi(ModelRestApi):
    resource_name = "ab_permission"
    datamodel = SQLAInterface(Ab_permission)

appbuilder.add_api(Ab_permissionApi)

class Ab_register_userApi(ModelRestApi):
    resource_name = "ab_register_user"
    datamodel = SQLAInterface(Ab_register_user)

appbuilder.add_api(Ab_register_userApi)

class Ab_roleApi(ModelRestApi):
    resource_name = "ab_role"
    datamodel = SQLAInterface(Ab_role)

appbuilder.add_api(Ab_roleApi)

class Ab_userApi(ModelRestApi):
    resource_name = "ab_user"
    datamodel = SQLAInterface(Ab_user)

appbuilder.add_api(Ab_userApi)

class Ab_view_menuApi(ModelRestApi):
    resource_name = "ab_view_menu"
    datamodel = SQLAInterface(Ab_view_menu)

appbuilder.add_api(Ab_view_menuApi)

class Agent_tierApi(ModelRestApi):
    resource_name = "agent_tier"
    datamodel = SQLAInterface(Agent_tier)

appbuilder.add_api(Agent_tierApi)

class BankApi(ModelRestApi):
    resource_name = "bank"
    datamodel = SQLAInterface(Bank)

appbuilder.add_api(BankApi)

class Biller_categoryApi(ModelRestApi):
    resource_name = "biller_category"
    datamodel = SQLAInterface(Biller_category)

appbuilder.add_api(Biller_categoryApi)

class Contact_typeApi(ModelRestApi):
    resource_name = "contact_type"
    datamodel = SQLAInterface(Contact_type)

appbuilder.add_api(Contact_typeApi)

class CountryApi(ModelRestApi):
    resource_name = "country"
    datamodel = SQLAInterface(Country)

appbuilder.add_api(CountryApi)

class CouponApi(ModelRestApi):
    resource_name = "coupon"
    datamodel = SQLAInterface(Coupon)

appbuilder.add_api(CouponApi)

class CurrencyApi(ModelRestApi):
    resource_name = "currency"
    datamodel = SQLAInterface(Currency)

appbuilder.add_api(CurrencyApi)

class Customer_segmentApi(ModelRestApi):
    resource_name = "customer_segment"
    datamodel = SQLAInterface(Customer_segment)

appbuilder.add_api(Customer_segmentApi)

class Doc_typeApi(ModelRestApi):
    resource_name = "doc_type"
    datamodel = SQLAInterface(Doc_type)

appbuilder.add_api(Doc_typeApi)

class Mime_typeApi(ModelRestApi):
    resource_name = "mime_type"
    datamodel = SQLAInterface(Mime_type)

appbuilder.add_api(Mime_typeApi)

class Mime_type_mapApi(ModelRestApi):
    resource_name = "mime_type_map"
    datamodel = SQLAInterface(Mime_type_map)

appbuilder.add_api(Mime_type_mapApi)

class Payment_cardApi(ModelRestApi):
    resource_name = "payment_card"
    datamodel = SQLAInterface(Payment_card)

appbuilder.add_api(Payment_cardApi)

class PromotionApi(ModelRestApi):
    resource_name = "promotion"
    datamodel = SQLAInterface(Promotion)

appbuilder.add_api(PromotionApi)

class Token_providerApi(ModelRestApi):
    resource_name = "token_provider"
    datamodel = SQLAInterface(Token_provider)

appbuilder.add_api(Token_providerApi)

class Trans_routing_thresholdsApi(ModelRestApi):
    resource_name = "trans_routing_thresholds"
    datamodel = SQLAInterface(Trans_routing_thresholds)

appbuilder.add_api(Trans_routing_thresholdsApi)

class Trans_typeApi(ModelRestApi):
    resource_name = "trans_type"
    datamodel = SQLAInterface(Trans_type)

appbuilder.add_api(Trans_typeApi)

class User_extApi(ModelRestApi):
    resource_name = "user_ext"
    datamodel = SQLAInterface(User_ext)

appbuilder.add_api(User_extApi)

class Ab_permission_viewApi(ModelRestApi):
    resource_name = "ab_permission_view"
    datamodel = SQLAInterface(Ab_permission_view)

appbuilder.add_api(Ab_permission_viewApi)

class Ab_user_roleApi(ModelRestApi):
    resource_name = "ab_user_role"
    datamodel = SQLAInterface(Ab_user_role)

appbuilder.add_api(Ab_user_roleApi)

class BillerApi(ModelRestApi):
    resource_name = "biller"
    datamodel = SQLAInterface(Biller)

appbuilder.add_api(BillerApi)

class StateApi(ModelRestApi):
    resource_name = "state"
    datamodel = SQLAInterface(State)

appbuilder.add_api(StateApi)

class TokenApi(ModelRestApi):
    resource_name = "token"
    datamodel = SQLAInterface(Token)

appbuilder.add_api(TokenApi)

class Ab_permission_view_roleApi(ModelRestApi):
    resource_name = "ab_permission_view_role"
    datamodel = SQLAInterface(Ab_permission_view_role)

appbuilder.add_api(Ab_permission_view_roleApi)

class Biller_offeringApi(ModelRestApi):
    resource_name = "biller_offering"
    datamodel = SQLAInterface(Biller_offering)

appbuilder.add_api(Biller_offeringApi)

class LgaApi(ModelRestApi):
    resource_name = "lga"
    datamodel = SQLAInterface(Lga)

appbuilder.add_api(LgaApi)

class AgentApi(ModelRestApi):
    resource_name = "agent"
    datamodel = SQLAInterface(Agent)

appbuilder.add_api(AgentApi)

class PosApi(ModelRestApi):
    resource_name = "pos"
    datamodel = SQLAInterface(Pos)

appbuilder.add_api(PosApi)

class Agent_pos_linkApi(ModelRestApi):
    resource_name = "agent_pos_link"
    datamodel = SQLAInterface(Agent_pos_link)

appbuilder.add_api(Agent_pos_linkApi)

class Comm_refApi(ModelRestApi):
    resource_name = "comm_ref"
    datamodel = SQLAInterface(Comm_ref)

appbuilder.add_api(Comm_refApi)

class PersonApi(ModelRestApi):
    resource_name = "person"
    datamodel = SQLAInterface(Person)

appbuilder.add_api(PersonApi)

class WalletApi(ModelRestApi):
    resource_name = "wallet"
    datamodel = SQLAInterface(Wallet)

appbuilder.add_api(WalletApi)

class Agent_person_linkApi(ModelRestApi):
    resource_name = "agent_person_link"
    datamodel = SQLAInterface(Agent_person_link)

appbuilder.add_api(Agent_person_linkApi)

class ContactApi(ModelRestApi):
    resource_name = "contact"
    datamodel = SQLAInterface(Contact)

appbuilder.add_api(ContactApi)

class DocApi(ModelRestApi):
    resource_name = "doc"
    datamodel = SQLAInterface(Doc)

appbuilder.add_api(DocApi)

class Person_additional_dataApi(ModelRestApi):
    resource_name = "person_additional_data"
    datamodel = SQLAInterface(Person_additional_data)

appbuilder.add_api(Person_additional_dataApi)

class Person_admin_dataApi(ModelRestApi):
    resource_name = "person_admin_data"
    datamodel = SQLAInterface(Person_admin_data)

appbuilder.add_api(Person_admin_dataApi)

class TransApi(ModelRestApi):
    resource_name = "trans"
    datamodel = SQLAInterface(Trans)

appbuilder.add_api(TransApi)

class Agent_doc_linkApi(ModelRestApi):
    resource_name = "agent_doc_link"
    datamodel = SQLAInterface(Agent_doc_link)

appbuilder.add_api(Agent_doc_linkApi)

class Person_doc_linkApi(ModelRestApi):
    resource_name = "person_doc_link"
    datamodel = SQLAInterface(Person_doc_link)

appbuilder.add_api(Person_doc_linkApi)
