"""
Mapa de rotas do PetHub
=======================
  publico  ->  /                         site da loja (vitrine)
               /servicos                 lista de serviços e preços
  auth     ->  /login  /logout  /cadastro  /painel (leva cada perfil à sua área)
  portal   ->  /cliente/...              área do CLIENTE (só enxerga o que é dele)
  admin    ->  /admin/                   painel da EQUIPE
               /admin/clientes|pets|servicos|agendamentos|usuarios   (CRUDs, via modulos.py)
"""
from rotas.publico import bp as publico_bp
from rotas.auth import bp as auth_bp
from rotas.portal import bp as portal_bp
from rotas.admin import bp as admin_bp

BLUEPRINTS = [publico_bp, auth_bp, portal_bp, admin_bp]
