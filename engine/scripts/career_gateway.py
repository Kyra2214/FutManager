from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine.manager.career import ManagerService
from engine.economy.staff_market import DEPARTMENTS, StaffMarketService
from engine.sports.training import TrainingService
from engine.sports.form_morale import FormMoraleService
from engine.sports.health import HealthService
from engine.ai.club_ai import ClubAI, Personality
from engine.transfers.market import TransferMarketService
from engine.world.simulation import WorldSimulationService, SimulationLevel
from engine.scouting.service import ScoutService
from engine.world.time_and_finance import WorldTickContext, FinanceLedger
from engine.players.contracts import PlayerContractService
from engine.economy.sponsorships import SponsorshipService
from engine.economy.travel_costs import TravelCostService
from engine.economy.world_economy import WorldEconomyService, EconomyService
from engine.events.service import ClubEventService
from engine.core.roadmap_gate import RoadmapGate, RoadmapGateError
from engine.core.domain_errors import DomainError, error_code
from engine.core.payload_contract import validate_payload, payload_fingerprint
from engine.core.p0_contracts import audit_p0_contracts, protect_p0_mutation, read_p0_contracts, validate_p0_contract
from engine.core.p1_procedure_contract import audit_p1_procedures, protect_p1_procedure_mutation, read_p1_procedures, validate_p1_procedure
from engine.core.p1_error_contract import audit_p1_errors, protect_p1_error_mutation, read_p1_errors, validate_p1_error
from engine.core.p1_version_contract import audit_p1_versions, protect_p1_version_mutation, read_p1_versions, validate_p1_version
from engine.core.p1_migration_contract import audit_p1_migrations, protect_p1_migration_mutation, read_p1_migrations, validate_p1_migration
from engine.core.p1_domain_version_contract import audit_p1_domain_versions, protect_p1_domain_version_mutation, read_p1_domain_versions, validate_p1_domain_version
from engine.core.p1_timeout_contract import audit_p1_timeouts, protect_p1_timeout_mutation, read_p1_timeouts, validate_p1_timeout
from engine.core.p1_telemetry_contract import audit_p1_telemetry, protect_p1_telemetry_mutation, read_p1_telemetry_contracts, read_p1_telemetry_events, record_p1_telemetry_event, validate_p1_telemetry
from engine.social.attendance import AttendanceService
from engine.social.stadium_fans import SocialService
from engine.stadiums.service import StadiumService
from engine.world.weekly_cycle import WeeklyWorldCycleService


def asset_url(relative_path: str | None) -> str | None:
    if not relative_path or not relative_path.startswith("assets/") or ".." in relative_path:
        return None
    return "/engine-assets/" + "/".join(relative_path.removeprefix("assets/").split("/"))


def catalog(connection: sqlite3.Connection, payload: dict) -> dict:
    entity_type = payload.get("entity_type", "club")
    search = str(payload.get("search", "")).strip()
    limit = min(max(int(payload.get("limit", 48)), 1), 96)
    if entity_type == "world_country":
        return {"items": ManagerService(connection).list_world_countries(search, limit)}
    if entity_type == "club":
        rows = connection.execute(
            """
            SELECT team.time_id AS entity_id, team.nome AS entity_name, team.pais_id AS country_id,
                   link.mapping_status, crest.relative_path AS crest_path,
                   mini.relative_path AS mini_crest_path, NULL AS kit_path
            FROM times team
            LEFT JOIN team_asset_links link ON link.time_id = team.time_id
            LEFT JOIN asset_catalog crest ON crest.asset_id = link.crest_asset_id
            LEFT JOIN asset_catalog mini ON mini.asset_id = link.crest_mini_asset_id
            WHERE trim(COALESCE(team.nome, '')) <> ''
              AND lower(trim(team.nome)) NOT LIKE 'sem contrato%'
              AND EXISTS (SELECT 1 FROM team_asset_links valid_link WHERE valid_link.time_id = team.time_id AND (valid_link.crest_asset_id IS NOT NULL OR valid_link.crest_mini_asset_id IS NOT NULL))
              AND (? = '' OR lower(team.nome) LIKE lower(?) OR lower(team.arquivo_origem) LIKE lower(?))
            ORDER BY team.nome COLLATE NOCASE, team.time_id
            LIMIT ?
            """,
            (search, f"%{search}%", f"%{search}%", limit),
        ).fetchall()
    elif entity_type == "selection":
        rows = connection.execute(
            """
            SELECT selection.selecao_id AS entity_id, selection.nome AS entity_name,
                   link.crest_status AS mapping_status, crest.relative_path AS crest_path,
                   NULL AS mini_crest_path, kit.relative_path AS kit_path
            FROM selecoes selection
            LEFT JOIN selection_asset_links link ON link.selecao_id = selection.selecao_id
            LEFT JOIN asset_catalog crest ON crest.asset_id = link.crest_asset_id
            LEFT JOIN asset_catalog kit ON kit.asset_id = link.primary_kit_asset_id
            WHERE (? = '' OR lower(selection.nome) LIKE lower(?) OR lower(selection.codigo) LIKE lower(?))
            ORDER BY selection.codigo, selection.selecao_id
            LIMIT ?
            """,
            (search, f"%{search}%", f"%{search}%", limit),
        ).fetchall()
    else:
        raise ValueError("CAREER_TARGET_INVALID")

    return {
        "items": [
            {
                "entityId": int(row["entity_id"]),
                "name": row["entity_name"],
                "countryId": int(row["country_id"]) if "country_id" in row.keys() and row["country_id"] is not None else None,
                "mappingStatus": row["mapping_status"] or ("SOURCE_NOT_PROVIDED" if entity_type == "selection" else "NO_SOURCE_ASSET"),
                "assetUrl": asset_url(row["crest_path"] or row["mini_crest_path"] or row["kit_path"]),
                "assetKind": "crest" if row["crest_path"] or row["mini_crest_path"] else "kit" if row["kit_path"] else None,
            }
            for row in rows
        ]
    }


def current(connection: sqlite3.Connection) -> dict:
    row = connection.execute(
        """
        SELECT career.career_id, career.name AS career_name, career.starting_division,
               manager.manager_id, manager.name AS manager_name,
               career.current_club_id, team.nome AS club_name,
               assignment.selection_id, selection.nome AS selection_name
        FROM manager_careers career
        INNER JOIN managers manager ON manager.manager_id = career.manager_id
        LEFT JOIN times team ON team.time_id = career.current_club_id
        LEFT JOIN manager_selection_assignments assignment ON assignment.career_id = career.career_id AND assignment.status = 'ACTIVE'
        LEFT JOIN selecoes selection ON selection.selecao_id = assignment.selection_id
        WHERE career.status = 'ACTIVE'
        ORDER BY career.updated_at DESC, career.career_id DESC
        LIMIT 1
        """
    ).fetchone()
    if row is None:
        return {"started": False}
    career_id = int(row["career_id"])
    config = connection.execute('SELECT combined_name,starting_division FROM career_world_configs WHERE career_id=?', (career_id,)).fetchone()
    countries = connection.execute('SELECT country_id,country_name,country_code FROM career_world_countries WHERE career_id=? ORDER BY country_id', (career_id,)).fetchall()
    parallel = connection.execute('SELECT name,total_clubs,source_country_count,seed,division_count FROM career_parallel_leagues WHERE career_id=?', (career_id,)).fetchone()
    world = {
        "combinedLeagueName": config["combined_name"] if config else None,
        "selectedCountryIds": [int(country["country_id"]) for country in countries],
        "selectedCountries": [{"countryId": int(country["country_id"]), "name": country["country_name"], "code": country["country_code"]} for country in countries],
        "startingDivision": int(config["starting_division"] if config else row["starting_division"] or 4),
        "parallelLeague": {"name": parallel["name"], "totalClubs": int(parallel["total_clubs"]), "sourceCountryCount": int(parallel["source_country_count"]), "seed": parallel["seed"], "divisionCount": int(parallel["division_count"])} if parallel else None,
    }
    if row["selection_id"] is not None:
        return {"started": True, "careerId": career_id, "managerId": int(row["manager_id"]), "managerName": row["manager_name"], "careerName": row["career_name"], "targetType": "selection", "targetId": int(row["selection_id"]), "targetName": row["selection_name"], **world}
    return {"started": True, "careerId": career_id, "managerId": int(row["manager_id"]), "managerName": row["manager_name"], "careerName": row["career_name"], "targetType": "club", "targetId": int(row["current_club_id"]), "targetName": row["club_name"], **world}


def current_club_id(connection: sqlite3.Connection) -> int:
    state = current(connection)
    if not state.get("started"):
        raise ValueError("CAREER_NOT_STARTED")
    if state.get("targetType") != "club":
        raise ValueError("CLUB_CAREER_REQUIRED")
    return int(state["targetId"])


def staff_market(connection: sqlite3.Connection, action: str, payload: dict) -> dict:
    club_id = current_club_id(connection)
    market = StaffMarketService(connection)
    if action == "economy_bootstrap":
        return market.bootstrap_club(club_id)
    if action == "economy_summary":
        return market.summary(club_id)
    if action == "staff_catalog":
        market.bootstrap_club(club_id)
        return {"items": market.available_staff(club_id, payload.get("role"))}
    if action == "staff_hire":
        return market.hire_staff(club_id, int(payload.get("staff_id")))
    if action == "staff_contract":
        return market.staff_contract(club_id, int(payload.get("staff_id")))
    if action == "staff_terminate":
        return market.terminate_staff(club_id, int(payload.get("staff_id")), bool(payload.get("waive_fee", False)))
    if action == "staff_replace":
        return market.replace_staff(club_id, int(payload.get("outgoing_staff_id")), int(payload.get("incoming_staff_id")))
    if action == "department_offers":
        market.bootstrap_club(club_id)
        return {"items": [market.department_offer(club_id, key) for key in DEPARTMENTS]}
    if action == "department_upgrade":
        return market.upgrade_department(club_id, str(payload.get("department")))
    if action == "economy_weekly":
        return market.process_weekly_costs(club_id)
    raise ValueError("STAFF_MARKET_ACTION_INVALID")


def contract_market(connection: sqlite3.Connection, action: str, payload: dict) -> dict:
    club_id = current_club_id(connection)
    if action != "contract_renew_approve":
        raise ValueError("CONTRACT_ACTION_INVALID")
    service = PlayerContractService(connection)
    try:
        return service.approve_renewal(
            player_id=int(payload.get("player_id")),
            club_id=club_id,
            season=int(payload.get("season")),
            week=int(payload.get("week")),
            weekly_salary=int(payload.get("weekly_salary")),
            duration_weeks=int(payload.get("duration_weeks", 52)),
            signing_fee=int(payload.get("signing_fee", 0)),
            bonus=int(payload.get("bonus", 0)),
            manager_approved=bool(payload.get("manager_approved", False)),
            tick_id=payload.get("tick_id"),
        )
    finally:
        service.close()


def finance_market(connection: sqlite3.Connection, action: str, payload: dict) -> dict:
    club_id=current_club_id(connection); economy=EconomyService(connection); travel=TravelCostService(connection)
    if action=='finance_revenue': return {'items': economy.report_revenue(club_id,payload.get('season'))}
    if action=='finance_expense': return {'items': economy.report_expense(club_id,payload.get('season'))}
    if action=='finance_budget': return {'budget': economy.budget(club_id,int(payload.get('projected_revenue',0)),int(payload.get('projected_expenses',0))).__dict__}
    if action=='finance_expense_preview': return economy.preview_expense(club_id,int(payload.get('amount',0)),str(payload.get('category','OTHER')))
    if action=='finance_post_match_preview': return economy.post_match_projection(club_id,int(payload.get('matchday_revenue',0)),int(payload.get('matchday_expense',0)))
    if action=='finance_projection': return economy.projection_39_weeks(club_id,int(payload.get('weekly_revenue',0)),int(payload.get('weekly_expenses',0)))
    if action=='finance_alert': return economy.low_balance_alert(club_id,int(payload.get('threshold_weeks',4)))
    if action=='finance_world_report': return economy.report_world(payload.get('season'))
    if action=='finance_audit': return economy.audit_season(int(payload.get('season')))
    if action=='travel_preview': return travel.preview(int(payload.get('match_id')), payload.get('club_id'))
    if action=='travel_summary': return travel.club_summary(club_id, payload.get('season'))
    if action=='finance_monthly_close': return FinanceLedger(connection).monthly_close(club_id, int(payload.get('season')), int(payload.get('month')))
    if action=='finance_reconciliation': return FinanceLedger(connection).cross_domain_reconciliation(club_id, int(payload.get('season')), payload.get('source_types'))
    if action=='finance_media_summary': return FinanceLedger(connection).media_revenue_summary(club_id, int(payload.get('season')))
    raise ValueError('FINANCE_ACTION_INVALID')


def scouting_market(connection: sqlite3.Connection, action: str, payload: dict) -> dict:
    club_id=current_club_id(connection); scout=ScoutService(connection)
    if action=='scout_regions': return {'items':[dict(row) for row in scout.regions()]}
    if action=='scout_create_region': scout.create_region(str(payload.get('region')),float(payload.get('cost_multiplier',1))); return {'ok':True}
    if action=='scout_mission': return {'mission_id':scout.create_mission(club_id,int(payload.get('scout_id')),str(payload.get('start_date')),int(payload.get('duration_months')),payload.get('region'),payload.get('position_code'),payload.get('min_age'),payload.get('max_age'),payload.get('min_strength'),payload.get('min_potential'),payload.get('seed'),int(payload.get('priority',50)))}
    if action=='scout_start': scout.start(int(payload.get('mission_id'))); return {'ok':True}
    if action=='scout_complete': return {'items':[dict(row) for row in scout.complete(int(payload.get('mission_id')),payload.get('as_of'),int(payload.get('limit',20)))]}
    if action=='scout_opportunities': return {'items':[dict(row) for row in scout.opportunities(int(payload.get('mission_id')),payload.get('position_code'),payload.get('min_age'),payload.get('max_age'),payload.get('min_potential'))]}
    if action=='scout_compare': return scout.compare(int(payload.get('opportunity_id')))
    if action=='scout_confirm': return scout.confirm_recruitment(int(payload.get('opportunity_id')),bool(payload.get('approved')))
    if action=='academy_enroll': return scout.academy_enroll(int(payload.get('player_id')),club_id,int(payload.get('maintenance_cost',0)))
    if action=='academy_progress': return scout.academy_progress(int(payload.get('player_id')),float(payload.get('amount',0)))
    if action=='academy_promote': return scout.academy_promote(int(payload.get('player_id')),bool(payload.get('approved')))
    if action=='academy_maintenance': return {'items':[dict(row) for row in scout.academy_maintenance(club_id)]}
    raise ValueError('SCOUTING_ACTION_INVALID')


def simulation_market(connection: sqlite3.Connection, action: str, payload: dict) -> dict:
    service = WorldSimulationService(connection)
    if action == 'simulation_configure': return service.configure(int(payload.get('season')), str(payload.get('level', 'ABSTRACT')), int(payload.get('seed', 0)))
    if action == 'simulation_batch': return service.simulate_batch(str(payload.get('tick_id')), str(payload.get('level', 'ABSTRACT')), int(payload.get('batch_size', 100)), int(payload.get('seed', 0)))
    if action == 'simulation_progress': return service.progress(str(payload.get('tick_id')))
    if action == 'simulation_checkpoint': return service.checkpoint(str(payload.get('tick_id')), int(payload.get('processed')), payload.get('last_match_id'), payload.get('state_hash'))
    if action == 'simulation_divergence': return service.divergence_report(str(payload.get('expected_tick_id')), str(payload.get('actual_tick_id')))
    if action == 'simulation_benchmark': return service.benchmark(int(payload.get('season')), str(payload.get('level', 'ABSTRACT')), int(payload.get('sample_size', 0)))
    if action == 'simulation_resume': return service.resume(str(payload.get('tick_id')), str(payload.get('level', 'ABSTRACT')), int(payload.get('batch_size', 100)), int(payload.get('seed', 0)))
    if action == 'simulation_metrics': return service.batch_metrics(str(payload.get('tick_id')))
    if action == 'simulation_failure_report': return service.failure_report(str(payload.get('tick_id')))
    raise ValueError('SIMULATION_ACTION_INVALID')


def transfer_market(connection: sqlite3.Connection, action: str, payload: dict) -> dict:
    club_id = current_club_id(connection); market = TransferMarketService(connection)
    if action == 'transferable_players': return {'items': [dict(row) for row in market.transferable_players(club_id, payload.get('age_min'), payload.get('age_max'), payload.get('position_code'), payload.get('min_strength'), payload.get('max_budget'))]}
    if action == 'transfer_history': return {'items': [dict(row) for row in market.negotiation_history(int(payload.get('offer_id')))]}
    if action == 'transfer_alerts': return {'items': [dict(row) for row in market.negotiation_alerts(club_id)]}
    if action == 'transfer_expire': return {'expired': market.expire_offers(str(payload.get('as_of')))}
    if action == 'transfer_open_window': return {'window_id': market.open_window(int(payload.get('season')), int(payload.get('number')), str(payload.get('start_date')), str(payload.get('end_date')), payload.get('rules'))}
    if action == 'transfer_preview': return market.preview_offer(club_id, int(payload.get('value',0)), int(payload.get('salary',0)), int(payload.get('commission',0)), int(payload.get('accessory_cost',0)))
    if action == 'transfer_offer': return {'offer_id': market.create_offer(int(payload.get('player_id')), club_id, int(payload.get('seller_club_id')), int(payload.get('value')), int(payload.get('window_id')), payload.get('asking_price'), payload.get('valid_until'), int(payload.get('salary',0)), int(payload.get('commission',0)), int(payload.get('accessory_cost',0)), bool(payload.get('international', False)))}
    if action == 'transfer_counter': return {'status': market.counter(int(payload.get('offer_id')), int(payload.get('value')))}
    if action == 'transfer_accept': return {'status': market.accept(int(payload.get('offer_id')))}
    if action == 'transfer_approve': return {'status': market.approve_offer(int(payload.get('offer_id')), str(payload.get('approved_by','manager')))}
    if action == 'transfer_loan': return {'loan_id': market.create_loan(int(payload.get('player_id')), int(payload.get('from_club_id')), club_id, str(payload.get('start_date')), str(payload.get('end_date')), int(payload.get('loan_fee',0)), payload.get('option_fee'), payload.get('option_deadline'))}
    if action == 'transfer_complete':
        context=WorldTickContext(str(payload.get('tick_id','transfer')), __import__('datetime').date.fromisoformat(str(payload.get('transfer_date','2026-01-01'))), int(payload.get('season',2026)), int(payload.get('week',1)), 1, 'week', payload.get('seed'))
        return {'status': market.complete(int(payload.get('offer_id')), context)}
    raise ValueError('TRANSFER_MARKET_ACTION_INVALID')


def club_ai_market(connection: sqlite3.Connection, action: str, payload: dict) -> dict:
    club_id = current_club_id(connection); ai = ClubAI(connection)
    if action == "ai_diagnosis": return ai.diagnostic_payload(club_id)
    if action == "ai_history": return {"items": [dict(row) for row in ai.history(club_id)]}
    if action == "ai_training": return {"decision": ai.propose_training(club_id)}
    if action == "ai_market": return {"decision": ai.propose_market(club_id, payload.get("seed"))}
    if action == "ai_weekly": return ai.weekly_cycle(club_id, payload.get("seed"))
    if action == "ai_lineup": return ai.auto_lineup(club_id, payload.get("seed"))
    if action == "ai_tactic": return {"decision": ai.choose_tactic(club_id, payload.get("seed"))}
    if action == "ai_objective_progress": return ai.update_objective(int(payload.get("objective_id")), float(payload.get("progress")))
    if action == "ai_preview": return ai.preview_decision(club_id, str(payload.get('type')), str(payload.get('decision')), payload.get('target'), int(payload.get('cost', 0)), int(payload.get('season', 2026)))
    if action == "ai_approve": return ai.approve_decision(int(payload.get('decision_id')), str(payload.get('approved_by', 'manager')))
    if action == "ai_risk_limit": return ai.set_risk_limit(club_id, int(payload.get('season', 2026)), int(payload.get('max_cost')), int(payload.get('max_aggressiveness', 50)))
    if action == "ai_budget_alerts": return {'items': [dict(row) for row in ai.budget_alerts(club_id, int(payload.get('season', 2026)))]}
    raise ValueError("AI_ACTION_INVALID")


def health_market(connection: sqlite3.Connection, action: str, payload: dict) -> dict:
    club_id = current_club_id(connection); service = HealthService(connection)
    if action == "health_list": return {"items": service.list_health(club_id, payload.get("severity"), payload.get("max_days"))}
    if action == "health_alerts": return {"items": service.alerts(club_id)}
    if action == "health_injury": return service.register_injury(club_id, int(payload.get("player_id")), str(payload.get("injury_type")), str(payload.get("severity")), int(payload.get("season")), int(payload.get("week")), payload.get("seed"))
    if action == "health_recover": return {"items": service.recover(club_id, int(payload.get("days", 1)))}
    if action == "health_suspension": return service.register_suspension(club_id, int(payload.get("player_id")), int(payload.get("cards", 0)), bool(payload.get("red_card", False)), int(payload.get("season")), int(payload.get("week")))
    raise ValueError("HEALTH_ACTION_INVALID")


def form_morale_market(connection: sqlite3.Connection, action: str, payload: dict) -> dict:
    club_id = current_club_id(connection)
    service = FormMoraleService(connection)
    if action == "morale_summary":
        return service.collective_morale(club_id)
    if action == "morale_match":
        return service.update_after_match(club_id, str(payload.get("result")), int(payload.get("season")), int(payload.get("week")), payload.get("seed"))
    if action == "weekly_training":
        return service.apply_weekly_training(club_id, int(payload.get("season")), int(payload.get("week")), str(payload.get("plan_type")), int(payload.get("load", 50)), payload.get("seed"), int(payload.get("international_matches", 0)))
    if action == "opponent_preparation":
        return service.create_opponent_preparation(club_id, int(payload.get("opponent_id")), int(payload.get("season")), int(payload.get("week")), str(payload.get("focus", "")))
    if action == "weekly_load":
        return service.weekly_load_report(club_id, int(payload.get("season")), int(payload.get("week")))
    if action == "form_recommendations":
        return {"items": service.recommendations(club_id)}
    raise ValueError("FORM_MORALE_ACTION_INVALID")


def training_market(connection: sqlite3.Connection, action: str, payload: dict) -> dict:
    club_id = current_club_id(connection)
    service = TrainingService(connection)
    if action == "training_departments":
        return {"items": service.department_inventory(club_id)}
    if action == "training_budget":
        return {"items": service.budget(club_id)}
    if action == "training_plan":
        return service.create_weekly_plan(club_id, int(payload.get("season")), int(payload.get("week")), str(payload.get("plan_type", "GENERAL")), int(payload.get("load", 50)))
    if action == "training_objective":
        return service.create_objective(club_id, int(payload.get("player_id")), int(payload.get("season")), str(payload.get("metric")), float(payload.get("target")))
    if action == "training_preview":
        return service.preview_plan(int(payload.get("plan_id")))
    if action == "training_approve":
        return service.approve_plan(int(payload.get("plan_id")), int(payload.get("version", 1)))
    if action == "training_cancel":
        return service.cancel_plan(int(payload.get("plan_id")), int(payload.get("version", 1)))
    if action == "training_development":
        return {"items": service.individual_development(club_id)}
    if action == "training_alerts":
        return {"items": service.maintenance_alerts(club_id)}
    raise ValueError("TRAINING_ACTION_INVALID")


def sponsorship_market(connection: sqlite3.Connection, action: str, payload: dict) -> dict:
    club_id = current_club_id(connection)
    service = SponsorshipService(connection)
    if action == "sponsor_bootstrap":
        return service.bootstrap_club(club_id)
    if action == "sponsor_summary":
        return service.summary(club_id)
    if action == "sponsor_offers":
        return {"items": service.offers(club_id)}
    if action == "sponsor_accept":
        return service.accept_offer(club_id, int(payload.get("offer_id")))
    if action == "sponsor_weekly":
        return service.process_week(club_id)
    raise ValueError("SPONSORSHIP_ACTION_INVALID")


def stadium_market(connection: sqlite3.Connection, action: str, payload: dict) -> dict:
    club_id = current_club_id(connection)
    stadiums = StadiumService(connection)
    attendance = AttendanceService(connection)
    if action == "stadium_bootstrap":
        return stadiums.bootstrap_club(club_id)
    if action == "stadium_summary":
        stadium = stadiums.get_stadium(club_id)
        social = connection.execute("SELECT * FROM club_fan_base WHERE club_id=?", (club_id,)).fetchone()
        reputation = connection.execute("SELECT * FROM club_reputation WHERE club_id=?", (club_id,)).fetchone()
        ticket = connection.execute("SELECT base_price FROM ticket_price_configs WHERE club_id=?", (club_id,)).fetchone()
        attendance_rows = connection.execute("SELECT * FROM attendance_records WHERE club_id=? ORDER BY attendance_id DESC LIMIT 8", (club_id,)).fetchall()
        return {"initialized": stadium is not None, "stadium": stadium, "fan_base": dict(social) if social else None, "reputation": dict(reputation) if reputation else None, "ticket_price": int(ticket["base_price"]) if ticket else 35, "attendance": [dict(row) for row in attendance_rows]}
    if action == "stadium_preview":
        return stadiums.preview_stadium_upgrade(club_id, str(payload.get("component")))
    if action == "stadium_upgrade":
        return stadiums.upgrade_stadium_component(club_id, str(payload.get("component")))
    if action == "ticket_price":
        attendance.configure_ticket_price(club_id, int(payload.get("base_price")))
        return {"club_id": club_id, "base_price": int(payload.get("base_price"))}
    if action == "ticket_price_preview":
        return SocialService(connection).ticket_price_preview(club_id, int(payload.get("base_price")), int(payload.get("importance", 50)), int(payload.get("visitor_reputation", 30)))
    if action == "fan_segments":
        return SocialService(connection).fan_segments(club_id)
    if action == "social_timeline":
        return SocialService(connection).social_timeline(club_id, int(payload.get("limit", 25)), int(payload.get("offset", 0)))
    raise ValueError("STADIUM_ACTION_INVALID")


def club_events(connection: sqlite3.Connection, action: str, payload: dict) -> dict:
    club_id = current_club_id(connection)
    events = ClubEventService(connection)
    if action == "events_list":
        return events.list_for_club(club_id, limit=int(payload.get("limit", 20)), unread_only=bool(payload.get("unread_only", False)))
    if action == "events_mark_read":
        event_id = int(payload.get("event_id"))
        return {"event_id": event_id, "read": events.mark_read(club_id, event_id)}
    raise ValueError("CLUB_EVENTS_ACTION_INVALID")


def career_operations(connection: sqlite3.Connection, action: str, payload: dict) -> dict:
    state = current(connection)
    if not state.get('started'):
        raise ValueError('CAREER_NOT_STARTED')
    service = ManagerService(connection)
    manager_id = int(state['managerId'])
    career_id = int(state['careerId'])
    if action == 'career_snapshot':
        return {'snapshot_id': service.snapshot(career_id)}
    if action == 'career_snapshot_list':
        rows = connection.execute('SELECT snapshot_id, career_id, created_at, engine_version FROM career_snapshots WHERE career_id=? ORDER BY snapshot_id DESC LIMIT 20', (career_id,)).fetchall()
        return {'items': [dict(row) for row in rows]}
    if action == 'career_snapshot_hash':
        snapshot_id = int(payload.get('snapshot_id'))
        return {'snapshot_id': snapshot_id, 'hash': service.snapshot_hash(snapshot_id)}
    if action == 'career_snapshot_compare':
        return service.compare_snapshots(int(payload.get('left_id')), int(payload.get('right_id')))
    if action == 'career_snapshot_restore':
        return service.restore_selective(manager_id, int(payload.get('snapshot_id')), list(payload.get('fields') or []))
    if action == 'career_snapshot_audit':
        return {'items': service.recovery_audit(career_id)}
    raise ValueError('CAREER_OPERATION_INVALID')


def _roadmap_3000_guard(front: int, priority: str) -> dict:
    manifest_path = Path(__file__).resolve().parents[2] / "futmanager_frontend" / "docs" / "roadmap_3000_execucao.json"
    if not manifest_path.exists():
        raise RoadmapGateError("ROADMAP_3000_MANIFEST_NOT_FOUND")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RoadmapGateError("ROADMAP_3000_MANIFEST_INVALID") from error
    item = next((entry for entry in manifest.get("items", []) if int(entry.get("item_id", -1)) == front), None)
    if item is None:
        raise RoadmapGateError(f"ROADMAP_3000_ITEM_NOT_FOUND:{front}")
    if str(item.get("priority", "")).upper() != priority:
        raise RoadmapGateError(f"ROADMAP_PRIORITY_MISMATCH:{front}")
    gates = manifest.get("gates", {})
    if priority != "P0" and gates.get("P0_GLOBAL_GATE") != "OPEN":
        raise RoadmapGateError(f"{priority}_BLOCKED_UNTIL_P0_CONSOLIDATED")
    if priority == "P2" and gates.get("P1_GLOBAL_GATE") != "OPEN":
        raise RoadmapGateError("P2_BLOCKED_UNTIL_P1_STABLE")
    return {"priority": priority, "front": front, "allowed": True, "gate": gates, "manifest": "roadmap_3000_execucao.json"}


def roadmap_guard(payload: dict) -> dict:
    priority = str(payload.get("priority", "")).upper()
    if priority not in {"P0", "P1", "P2"}:
        raise ValueError("ROADMAP_PRIORITY_INVALID")
    configured_path = os.environ.get("FUTMANAGER_ROADMAP_GATE_PATH")
    gate_path = Path(configured_path) if configured_path else Path(__file__).resolve().parents[2] / "futmanager_frontend" / "roadmap_gate.json"
    gate = RoadmapGate(gate_path)
    front = payload.get("front")
    if front is not None and int(front) >= 941:
        return _roadmap_3000_guard(int(front), priority)
    if front is not None:
        gate.assert_front_allowed(int(front))  # dependency guard before real runtime execution
    else:
        gate.assert_allowed(priority)  # real runtime guard; no game-state write
    return {"priority": priority, "front": int(front) if front is not None else None, "allowed": True, "gate": gate.status()}


def p0_contract_market(connection: sqlite3.Connection, action: str, payload: dict) -> dict:
    if action == 'p0_contracts':
        return {'items': read_p0_contracts(connection, int(payload['domain_id']) if payload.get('domain_id') is not None else None), 'read_only': True}
    if action == 'p0_contract_validate':
        return validate_p0_contract(connection, int(payload.get('item_id')))
    if action == 'p0_contract_protect':
        return protect_p0_mutation(connection, int(payload.get('item_id')), str(payload.get('actor', '')), dict(payload.get('mutation') or {}))
    if action == 'p0_contract_audit':
        return audit_p0_contracts(connection)
    raise ValueError('P0_CONTRACT_ACTION_INVALID')


def p1_procedure_market(connection: sqlite3.Connection, action: str, payload: dict) -> dict:
    if action == 'p1_procedure_contracts':
        return {'items': read_p1_procedures(connection), 'read_only': True}
    if action == 'p1_procedure_validate':
        return validate_p1_procedure(connection, int(payload.get('item_id')))
    if action == 'p1_procedure_protect':
        return protect_p1_procedure_mutation(connection, int(payload.get('item_id')), str(payload.get('actor', '')), dict(payload.get('mutation') or {}))
    if action == 'p1_procedure_audit':
        return audit_p1_procedures(connection)
    raise ValueError('P1_PROCEDURE_ACTION_INVALID')


def p1_error_market(connection: sqlite3.Connection, action: str, payload: dict) -> dict:
    if action == 'p1_error_contracts':
        return {'items': read_p1_errors(connection), 'read_only': True}
    if action == 'p1_error_validate':
        return validate_p1_error(connection, int(payload.get('item_id')))
    if action == 'p1_error_protect':
        return protect_p1_error_mutation(connection, int(payload.get('item_id')), str(payload.get('actor', '')), dict(payload.get('mutation') or {}))
    if action == 'p1_error_audit':
        return audit_p1_errors(connection)
    raise ValueError('P1_ERROR_ACTION_INVALID')


def p1_version_market(connection: sqlite3.Connection, action: str, payload: dict) -> dict:
    if action == 'p1_version_contracts':
        return {'items': read_p1_versions(connection), 'read_only': True}
    if action == 'p1_version_validate':
        return validate_p1_version(connection, int(payload.get('item_id')))
    if action == 'p1_version_protect':
        return protect_p1_version_mutation(connection, int(payload.get('item_id')), str(payload.get('actor', '')), dict(payload.get('mutation') or {}))
    if action == 'p1_version_audit':
        return audit_p1_versions(connection)
    raise ValueError('P1_VERSION_ACTION_INVALID')


def p1_migration_market(connection: sqlite3.Connection, action: str, payload: dict) -> dict:
    if action == 'p1_migration_contracts':
        return {'items': read_p1_migrations(connection), 'read_only': True}
    if action == 'p1_migration_validate':
        return validate_p1_migration(connection, int(payload.get('item_id')))
    if action == 'p1_migration_protect':
        return protect_p1_migration_mutation(connection, int(payload.get('item_id')), str(payload.get('actor', '')), dict(payload.get('mutation') or {}))
    if action == 'p1_migration_audit':
        return audit_p1_migrations(connection)
    raise ValueError('P1_MIGRATION_ACTION_INVALID')


def p1_domain_version_market(connection: sqlite3.Connection, action: str, payload: dict) -> dict:
    if action == 'p1_domain_version_contracts': return {'items': read_p1_domain_versions(connection), 'read_only': True}
    if action == 'p1_domain_version_validate': return validate_p1_domain_version(connection, int(payload.get('item_id')))
    if action == 'p1_domain_version_protect': return protect_p1_domain_version_mutation(connection, int(payload.get('item_id')), str(payload.get('actor', '')), dict(payload.get('mutation') or {}))
    if action == 'p1_domain_version_audit': return audit_p1_domain_versions(connection)
    raise ValueError('P1_DOMAIN_VERSION_ACTION_INVALID')


def p1_telemetry_market(connection: sqlite3.Connection, action: str, payload: dict) -> dict:
    if action == 'p1_telemetry_contracts': return {'items': read_p1_telemetry_contracts(connection), 'read_only': True}
    if action == 'p1_telemetry_events': return {'items': read_p1_telemetry_events(connection, payload.get('career_id'), payload.get('limit', 100)), 'read_only': True}
    if action == 'p1_telemetry_validate': return validate_p1_telemetry(connection, int(payload.get('item_id')))
    if action == 'p1_telemetry_record': return record_p1_telemetry_event(connection, str(payload.get('event_key', '')), str(payload.get('event_name', '')), dict(payload.get('event_payload') or {}), payload.get('career_id'), payload.get('season_number'), payload.get('week_number'), str(payload.get('actor', '')))
    if action == 'p1_telemetry_protect': return protect_p1_telemetry_mutation(connection, int(payload.get('item_id')), str(payload.get('actor', '')), dict(payload.get('mutation') or {}))
    if action == 'p1_telemetry_audit': return audit_p1_telemetry(connection)
    raise ValueError('P1_TELEMETRY_ACTION_INVALID')
def p1_timeout_market(connection: sqlite3.Connection, action: str, payload: dict) -> dict:
    if action == 'p1_timeout_contracts': return {'items': read_p1_timeouts(connection), 'read_only': True}
    if action == 'p1_timeout_validate': return validate_p1_timeout(connection, int(payload.get('item_id')))
    if action == 'p1_timeout_protect': return protect_p1_timeout_mutation(connection, int(payload.get('item_id')), str(payload.get('actor', '')), dict(payload.get('mutation') or {}))
    if action == 'p1_timeout_audit': return audit_p1_timeouts(connection)
    raise ValueError('P1_TIMEOUT_ACTION_INVALID')


def parallel_market(connection: sqlite3.Connection, action: str, payload: dict) -> dict:
    state = current(connection)
    if not state.get('started'):
        raise ValueError('CAREER_NOT_STARTED')
    career_id = int(payload.get('career_id') or state['careerId'])
    service = ManagerService(connection)
    if action == 'parallel_snapshot':
        return service.parallel_league_snapshot(career_id, int(payload.get('season_number', 1)))
    if action == 'parallel_result':
        return service.record_parallel_result(career_id, int(payload.get('fixture_id')), int(payload.get('home_goals')), int(payload.get('away_goals')))
    if action == 'parallel_close':
        return service.close_parallel_season(career_id, int(payload.get('season_number', 1)))
    raise ValueError('PARALLEL_LEAGUE_ACTION_INVALID')


def run(action: str, payload: dict, database_path: Path) -> dict:
    if action == "roadmap_guard":
        return {"ok": True, **roadmap_guard(payload)}
    service = ManagerService(database_path)
    try:
        if action == "catalog":
            return {"ok": True, **catalog(service.connection, payload)}
        if action == "current":
            return {"ok": True, **current(service.connection)}
        if action in {"p0_contracts", "p0_contract_validate", "p0_contract_protect", "p0_contract_audit"}:
            return {"ok": True, **p0_contract_market(service.connection, action, payload)}
        if action in {"p1_procedure_contracts", "p1_procedure_validate", "p1_procedure_protect", "p1_procedure_audit"}:
            return {"ok": True, **p1_procedure_market(service.connection, action, payload)}
        if action in {"p1_error_contracts", "p1_error_validate", "p1_error_protect", "p1_error_audit"}:
            return {"ok": True, **p1_error_market(service.connection, action, payload)}
        if action in {"p1_version_contracts", "p1_version_validate", "p1_version_protect", "p1_version_audit"}:
            return {"ok": True, **p1_version_market(service.connection, action, payload)}
        if action in {"p1_migration_contracts", "p1_migration_validate", "p1_migration_protect", "p1_migration_audit"}:
            return {"ok": True, **p1_migration_market(service.connection, action, payload)}
        if action in {"p1_domain_version_contracts", "p1_domain_version_validate", "p1_domain_version_protect", "p1_domain_version_audit"}:
            return {"ok": True, **p1_domain_version_market(service.connection, action, payload)}
        if action in {"p1_timeout_contracts", "p1_timeout_validate", "p1_timeout_protect", "p1_timeout_audit"}:
            return {"ok": True, **p1_timeout_market(service.connection, action, payload)}
        if action in {"p1_telemetry_contracts", "p1_telemetry_events", "p1_telemetry_validate", "p1_telemetry_record", "p1_telemetry_protect", "p1_telemetry_audit"}:
            return {"ok": True, **p1_telemetry_market(service.connection, action, payload)}
        if action == "parallel_preview":
            return {"ok": True, **service.preview_parallel_league([int(value) for value in payload.get('selected_country_ids', [])], str(payload.get('target_type', 'club')), int(payload.get('target_id')))}
        if action in {"parallel_snapshot", "parallel_result", "parallel_close"}:
            return {"ok": True, **parallel_market(service.connection, action, payload)}
        if action == "start":
            result = service.start_career(
                manager_name=payload.get("manager_name"),
                nationality=payload.get("nationality"),
                age=payload.get("age"),
                career_name=payload.get("career_name"),
                target_type=payload.get("target_type"),
                target_id=payload.get("target_id"),
                selected_country_ids=payload.get("selected_country_ids"),
            )
            return {"ok": True, "started": True, **result}
        if action == "economy_bootstrap_all":
            return {"ok": True, **StaffMarketService(service.connection).bootstrap_all_clubs()}
        if action == "economy_weekly_all":
            return {"ok": True, **WorldEconomyService(service.connection).process_world_week()}
        if action == "sponsor_bootstrap_all":
            return {"ok": True, **SponsorshipService(service.connection).bootstrap_all_clubs()}
        if action == "sponsor_weekly_all":
            return {"ok": True, **SponsorshipService(service.connection).process_week_all()}
        if action == "stadium_bootstrap_all":
            return {"ok": True, **StadiumService(service.connection).bootstrap_all_clubs()}
        if action == "weekly_advance":
            current_club_id(service.connection)
            return {"ok": True, **WeeklyWorldCycleService(service.connection).advance_week(payload.get("seed"))}
        if action in {"economy_bootstrap", "economy_summary", "staff_catalog", "staff_hire", "staff_contract", "staff_terminate", "staff_replace", "department_offers", "department_upgrade", "economy_weekly"}:
            return {"ok": True, **staff_market(service.connection, action, payload)}
        if action in {"ai_diagnosis", "ai_history", "ai_training", "ai_market", "ai_weekly", "ai_lineup", "ai_tactic", "ai_objective_progress", "ai_preview", "ai_approve", "ai_risk_limit", "ai_budget_alerts"}:
            return {"ok": True, **club_ai_market(service.connection, action, payload)}
        if action in {"contract_renew_approve"}:
            return {"ok": True, **contract_market(service.connection, action, payload)}
        if action in {"finance_revenue", "finance_expense", "finance_budget", "finance_expense_preview", "finance_post_match_preview", "finance_projection", "finance_alert", "finance_world_report", "finance_audit", "travel_preview", "travel_summary", "finance_monthly_close", "finance_reconciliation", "finance_media_summary"}:
            return {"ok": True, **finance_market(service.connection, action, payload)}
        if action in {"scout_regions", "scout_create_region", "scout_mission", "scout_start", "scout_complete", "scout_opportunities", "scout_compare", "scout_confirm", "academy_enroll", "academy_progress", "academy_promote", "academy_maintenance"}:
            return {"ok": True, **scouting_market(service.connection, action, payload)}
        if action in {"simulation_configure", "simulation_batch", "simulation_progress", "simulation_checkpoint", "simulation_divergence", "simulation_benchmark", "simulation_resume", "simulation_metrics", "simulation_failure_report"}:
            return {"ok": True, **simulation_market(service.connection, action, payload)}
        if action in {"transferable_players", "transfer_open_window", "transfer_preview", "transfer_offer", "transfer_counter", "transfer_accept", "transfer_approve", "transfer_loan", "transfer_complete", "transfer_history", "transfer_alerts", "transfer_expire"}:
            return {"ok": True, **transfer_market(service.connection, action, payload)}
        if action in {"health_list", "health_alerts", "health_injury", "health_recover", "health_suspension"}:
            return {"ok": True, **health_market(service.connection, action, payload)}
        if action in {"morale_summary", "morale_match", "weekly_training", "opponent_preparation", "weekly_load", "form_recommendations"}:
            return {"ok": True, **form_morale_market(service.connection, action, payload)}
        if action in {"training_departments", "training_budget", "training_plan", "training_objective", "training_preview", "training_approve", "training_cancel", "training_development", "training_alerts"}:
            return {"ok": True, **training_market(service.connection, action, payload)}
        if action in {"sponsor_bootstrap", "sponsor_summary", "sponsor_offers", "sponsor_accept", "sponsor_weekly"}:
            return {"ok": True, **sponsorship_market(service.connection, action, payload)}
        if action in {"stadium_bootstrap", "stadium_summary", "stadium_preview", "stadium_upgrade", "ticket_price", "ticket_price_preview", "fan_segments", "social_timeline"}:
            return {"ok": True, **stadium_market(service.connection, action, payload)}
        if action in {"career_snapshot", "career_snapshot_list", "career_snapshot_hash", "career_snapshot_compare", "career_snapshot_restore", "career_snapshot_audit"}:
            return {"ok": True, **career_operations(service.connection, action, payload)}
        if action in {"events_list", "events_mark_read"}:
            return {"ok": True, **club_events(service.connection, action, payload)}
        raise ValueError("CAREER_ACTION_INVALID")
    finally:
        service.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["catalog", "current", "parallel_preview", "roadmap_guard", "p0_contracts", "p0_contract_validate", "p0_contract_protect", "p0_contract_audit", "p1_procedure_contracts", "p1_procedure_validate", "p1_procedure_protect", "p1_procedure_audit", "p1_error_contracts", "p1_error_validate", "p1_error_protect", "p1_error_audit", "p1_version_contracts", "p1_version_validate", "p1_version_protect", "p1_version_audit", "p1_migration_contracts", "p1_migration_validate", "p1_migration_protect", "p1_migration_audit", "p1_domain_version_contracts", "p1_domain_version_validate", "p1_domain_version_protect", "p1_domain_version_audit", "p1_timeout_contracts", "p1_timeout_validate", "p1_timeout_protect", "p1_timeout_audit", "start", "contract_renew_approve", "economy_bootstrap_all", "economy_weekly_all", "economy_bootstrap", "economy_summary", "staff_catalog", "staff_hire", "staff_contract", "staff_terminate", "staff_replace", "department_offers", "department_upgrade", "economy_weekly", "training_departments", "training_budget", "training_plan", "training_objective", "training_preview", "training_approve", "training_cancel", "training_development", "training_alerts", "morale_summary", "morale_match", "weekly_training", "opponent_preparation", "weekly_load", "form_recommendations", "health_list", "health_alerts", "health_injury", "health_recover", "health_suspension", "ai_diagnosis", "ai_history", "ai_training", "ai_market", "ai_weekly", "ai_lineup", "ai_tactic", "ai_objective_progress", "ai_preview", "ai_approve", "ai_risk_limit", "ai_budget_alerts", "transferable_players", "transfer_open_window", "transfer_preview", "transfer_offer", "transfer_counter", "transfer_accept", "transfer_approve", "transfer_loan", "transfer_complete", "transfer_history", "transfer_alerts", "transfer_expire", "simulation_configure", "simulation_batch", "simulation_progress", "simulation_checkpoint", "simulation_divergence", "simulation_benchmark", "simulation_resume", "simulation_metrics", "simulation_failure_report", "scout_regions", "scout_create_region", "scout_mission", "scout_start", "scout_complete", "scout_opportunities", "scout_compare", "scout_confirm", "academy_enroll", "academy_progress", "academy_promote", "academy_maintenance", "finance_revenue", "finance_expense", "finance_budget", "finance_expense_preview", "finance_post_match_preview", "finance_projection", "finance_alert", "finance_world_report", "finance_audit", "travel_preview", "travel_summary", "finance_monthly_close", "finance_reconciliation", "finance_media_summary", "sponsor_bootstrap_all", "sponsor_weekly_all", "sponsor_bootstrap", "sponsor_summary", "sponsor_offers", "sponsor_accept", "sponsor_weekly", "stadium_bootstrap", "stadium_bootstrap_all", "stadium_summary", "stadium_upgrade", "ticket_price", "ticket_price_preview", "fan_segments", "social_timeline", "weekly_advance", "events_list", "events_mark_read", "career_snapshot", "career_snapshot_list", "career_snapshot_hash", "career_snapshot_compare", "career_snapshot_restore", "career_snapshot_audit", "parallel_snapshot", "parallel_result", "parallel_close"])
    parser.add_argument("--database", default=str(ROOT / "data/state/game.db"))
    arguments = parser.parse_args()
    try:
        payload = validate_payload(arguments.action, json.loads(sys.stdin.read() or "{}"))
        result = run(arguments.action, payload, Path(arguments.database))
        if arguments.action.startswith("p0_contract") or arguments.action == "roadmap_guard":
            result.setdefault("payload_fingerprint", payload_fingerprint(arguments.action, payload))
        print(json.dumps(result, ensure_ascii=False))
    except (DomainError, ValueError, RoadmapGateError, sqlite3.Error) as error:
        print(json.dumps({"ok": False, "error": error_code(error)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
