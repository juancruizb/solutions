"""
Management command: sync_solutions
===================================
Fetches all solutions from SDP Cloud and upserts them into the local SQLite DB.
Run manually:
    python manage.py sync_solutions
Run as cron (every hour):
    0 * * * * /path/to/venv/bin/python manage.py sync_solutions
"""
import os
from django.core.management.base import BaseCommand
from django.db import transaction
from dotenv import load_dotenv

load_dotenv()


class Command(BaseCommand):
    help = 'Sync solutions and topics from SDP Cloud into local DB'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Fetch data but do not write to DB',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Print each solution as it is upserted',
        )

    def handle(self, *args, **options):
        from resources.token.sdp_auth import SDPAuth
        from resources.solutions.sdp_solutions import SDPSolutions
        from api.models import Topic, Solution

        dry_run = options['dry_run']
        verbose = options['verbose']

        self.stdout.write(self.style.MIGRATE_HEADING('── SDP Cloud Sync ──────────────────'))

        # 1. Get access token (cached in token_store.json — no rate-limit risk)
        self.stdout.write('  Obtaining access token...')
        token = SDPAuth.get_access_token(
            client_id=os.getenv('SDP_CLIENT_ID'),
            client_secret=os.getenv('SDP_CLIENT_SECRET'),
        )
        self.stdout.write(self.style.SUCCESS('  ✓ Token OK'))

        # 2. Fetch all solutions from SDP Cloud
        self.stdout.write('  Fetching solutions from SDP Cloud...')
        raw_solutions = SDPSolutions.get_all_paginated(token)
        self.stdout.write(self.style.SUCCESS(f'  ✓ {len(raw_solutions)} solutions fetched'))

        if dry_run:
            self.stdout.write(self.style.WARNING('  DRY RUN — no DB writes.'))
            return

        # 3. Upsert Topics then Solutions in a single transaction
        created_s = updated_s = created_t = updated_t = 0

        with transaction.atomic():
            for raw in raw_solutions:
                # ── Topic ────────────────────────────────────────────────
                raw_topic = raw.get('topic') or {}
                topic_obj = None
                if raw_topic.get('id'):
                    topic_obj, t_created = Topic.objects.update_or_create(
                        sdp_id=raw_topic['id'],
                        defaults={
                            'name':     raw_topic.get('name', ''),
                            'icon_key': raw_topic.get('folder_name', '') or '',
                        },
                    )
                    if t_created:
                        created_t += 1
                    else:
                        updated_t += 1

                # ── Solution ─────────────────────────────────────────────
                sdp_id = raw.get('id', '')
                if not sdp_id:
                    continue

                display_id = (raw.get('display_id') or {}).get('display_value', '')
                title      = raw.get('title', 'Sin título')
                author     = (raw.get('created_by') or {}).get('name', '')
                status     = (raw.get('approval_status') or {}).get('name', '')
                updated    = (raw.get('last_updated_time') or {}).get('display_value', '')
                hits       = int(raw.get('no_of_hits') or 0)
                keywords   = raw.get('keywords') or ''
                is_public  = raw.get('is_public', False)
                description = raw.get('description') or ''

                sol, s_created = Solution.objects.update_or_create(
                    sdp_id=sdp_id,
                    defaults={
                        'display_id':  display_id,
                        'title':       title,
                        'description': description,
                        'topic':       topic_obj,
                        'status':      status,
                        'author':      author,
                        'updated_sdp': updated,
                        'hits':        hits,
                        'keywords':    keywords,
                        'is_public':   is_public,
                    },
                )

                if s_created:
                    created_s += 1
                else:
                    updated_s += 1

                if verbose:
                    action = 'CREATE' if s_created else 'UPDATE'
                    self.stdout.write(f'    [{action}] {display_id} — {title[:60]}')

        # 4. Summary
        self.stdout.write('')
        self.stdout.write(self.style.MIGRATE_HEADING('── Summary ─────────────────────────'))
        self.stdout.write(f'  Topics  : {created_t} created · {updated_t} updated')
        self.stdout.write(f'  Solutions: {created_s} created · {updated_s} updated')
        self.stdout.write(self.style.SUCCESS('  ✓ Sync complete'))
