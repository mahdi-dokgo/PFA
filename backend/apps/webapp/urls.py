from django.contrib.auth.views import LogoutView
from django.urls import path

from .views import articles, audit, auth, consultations, dashboard, factures, orders, purchase_requests, receptions, stock, suppliers, users

app_name = 'webapp'

urlpatterns = [
    # Authentification
    path('login/', auth.WebLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # Tableau de bord
    path('', dashboard.DashboardView.as_view(), name='dashboard'),
    path('journal/', audit.AuditLogListView.as_view(), name='audit_log_list'),

    # Demandes d'achat
    path('demandes/export/excel/', purchase_requests.ExportDaExcelView.as_view(), name='export_da_excel'),
    path('demandes/export/pdf/', purchase_requests.ExportDaPdfView.as_view(), name='export_da_pdf'),
    path('demandes/', purchase_requests.PurchaseRequestListView.as_view(), name='request_list'),
    path('demandes/nouvelle/', purchase_requests.PurchaseRequestCreateView.as_view(), name='request_create'),
    path('demandes/<int:pk>/', purchase_requests.PurchaseRequestDetailView.as_view(), name='request_detail'),
    path('demandes/<int:pk>/soumettre/', purchase_requests.PurchaseRequestSubmitView.as_view(), name='request_submit'),
    path('demandes/<int:pk>/valider/', purchase_requests.PurchaseRequestApproveView.as_view(), name='request_approve'),
    path('demandes/<int:pk>/rejeter/', purchase_requests.PurchaseRequestRejectView.as_view(), name='request_reject'),

    # Fournisseurs
    path('fournisseurs/', suppliers.SupplierListView.as_view(), name='supplier_list'),
    path('fournisseurs/nouveau/', suppliers.SupplierCreateView.as_view(), name='supplier_create'),
    path('fournisseurs/<int:pk>/', suppliers.SupplierDetailView.as_view(), name='supplier_detail'),
    path('fournisseurs/<int:pk>/modifier/', suppliers.SupplierUpdateView.as_view(), name='supplier_update'),
    path('fournisseurs/<int:pk>/archiver/', suppliers.SupplierArchiveToggleView.as_view(), name='supplier_archive_toggle'),

    # Utilisateurs
    path('utilisateurs/', users.UserListView.as_view(), name='user_list'),
    path('utilisateurs/nouveau/', users.UserCreateView.as_view(), name='user_create'),
    path('utilisateurs/<int:pk>/modifier/', users.UserUpdateView.as_view(), name='user_update'),
    path('utilisateurs/<int:pk>/toggle/', users.UserToggleActiveView.as_view(), name='user_toggle'),
    path('utilisateurs/<int:pk>/supprimer/', users.UserDeleteView.as_view(), name='user_delete'),

    # Articles
    path('articles/', articles.ArticleListView.as_view(), name='article_list'),
    path('articles/nouveau/', articles.ArticleCreateView.as_view(), name='article_create'),
    path('articles/<int:pk>/modifier/', articles.ArticleUpdateView.as_view(), name='article_update'),
    path('articles/<int:pk>/supprimer/', articles.ArticleDeleteView.as_view(), name='article_delete'),

    # Catégories
    path('categories/', articles.CategoryListView.as_view(), name='category_list'),
    path('categories/nouvelle/', articles.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/modifier/', articles.CategoryUpdateView.as_view(), name='category_update'),
    path('categories/<int:pk>/supprimer/', articles.CategoryDeleteView.as_view(), name='category_delete'),

    # Bons de commande — exports
    path('bons-commande/export/excel/', orders.ExportBcExcelView.as_view(), name='export_bc_excel'),
    path('bons-commande/export/pdf/', orders.ExportBcPdfView.as_view(), name='export_bc_pdf'),
    path('bons-commande/<int:pk>/pdf/', orders.ExportBcDetailPdfView.as_view(), name='export_bc_detail_pdf'),

    # Bons de commande
    path('commandes/', orders.PurchaseOrderListView.as_view(), name='po_list'),
    path('commandes/nouvelle/', orders.PurchaseOrderCreateView.as_view(), name='po_create'),
    path('commandes/<int:pk>/', orders.PurchaseOrderDetailView.as_view(), name='po_detail'),
    path('commandes/<int:pk>/transition/', orders.PurchaseOrderTransitionView.as_view(), name='po_transition'),

    # Réceptions
    path('receptions/', receptions.ReceptionListView.as_view(), name='reception_list'),
    path('receptions/nouvelle/', receptions.ReceptionCreateView.as_view(), name='reception_create'),
    path('receptions/<int:pk>/', receptions.ReceptionDetailView.as_view(), name='reception_detail'),

    # Consultations
    path('consultations/', consultations.ConsultationListView.as_view(), name='consultation_list'),
    path('consultations/nouvelle/', consultations.ConsultationCreateView.as_view(), name='consultation_create'),
    path('consultations/<int:pk>/', consultations.ConsultationDetailView.as_view(), name='consultation_detail'),
    path('consultations/<int:pk>/proposition/<int:fournisseur_id>/', consultations.PropositionSaisirView.as_view(), name='proposition_saisir'),
    path('consultations/<int:pk>/retenir/<int:proposition_id>/', consultations.PropositionRetenirView.as_view(), name='proposition_retenir'),
    path('consultations/<int:pk>/cloturer/', consultations.ConsultationCloturerView.as_view(), name='consultation_cloturer'),

    # Factures — exports
    path('factures/export/excel/', factures.ExportFacturesExcelView.as_view(), name='export_factures_excel'),
    path('factures/export/pdf/', factures.ExportFacturesPdfView.as_view(), name='export_factures_pdf'),

    # Factures
    path('factures/', factures.FactureListView.as_view(), name='facture_list'),
    path('factures/nouvelle/', factures.FactureCreateView.as_view(), name='facture_create'),
    path('factures/<int:pk>/', factures.FactureDetailView.as_view(), name='facture_detail'),
    path('factures/<int:pk>/valider/', factures.FactureValiderView.as_view(), name='facture_valider'),
    path('factures/<int:pk>/payer/', factures.FacturePayerView.as_view(), name='facture_payer'),
    path('factures/<int:pk>/rejeter/', factures.FactureRejeterView.as_view(), name='facture_rejeter'),

    # Stock — exports
    path('stock/export/excel/', stock.ExportStockExcelView.as_view(), name='export_stock_excel'),

    # Stock
    path('stock/', stock.StockOverviewView.as_view(), name='stock_overview'),
    path('stock/mouvements/', stock.StockMovementListView.as_view(), name='stock_movements'),
    path('stock/ajustement/', stock.StockAdjustmentCreateView.as_view(), name='stock_adjustment_create'),
]
