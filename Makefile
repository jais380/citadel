.PHONY: up down restart logs ps smoke notify-test pipeline psql scorecard rebuild

up:            ## start the whole local stack
	docker compose up -d --build

down:          ## stop everything (data volumes are kept)
	docker compose down

restart:
	docker compose restart orchestrator

logs:          ## follow orchestrator + router logs
	docker compose logs -f orchestrator omniroute

ps:
	docker compose ps

smoke:         ## ping every model tier once
	docker compose exec orchestrator python -m app.smoke

notify-test:   ## send a test Telegram message
	docker compose exec orchestrator python -m app.notify

pipeline:      ## make pipeline TASK="..." [SCOPE=work]
	@test -n "$(TASK)" || (echo 'usage: make pipeline TASK="what to build"' && exit 1)
	docker compose exec orchestrator python -m app.pipeline_plain "$(TASK)" --scope $(or $(SCOPE),personal)

psql:          ## open a SQL shell
	docker compose exec postgres psql -U citadel -d citadel

scorecard:     ## reviewer rejection rate per developer model
	docker compose exec postgres psql -U citadel -d citadel -c "SELECT * FROM model_scorecard;"

rebuild:
	docker compose build --no-cache orchestrator && docker compose up -d orchestrator
