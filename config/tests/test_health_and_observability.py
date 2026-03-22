from django.test import Client, TestCase


class HealthEndpointsTests(TestCase):
    def test_live_returns_ok(self):
        r = self.client.get('/health/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {'status': 'ok'})

    def test_ready_returns_ok_with_db(self):
        r = self.client.get('/health/ready/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {'status': 'ok'})


class RequestIdTests(TestCase):
    def test_generates_x_request_id(self):
        c = Client()
        r = c.get('/health/')
        self.assertIn('X-Request-ID', r)
        self.assertEqual(len(r['X-Request-ID']), 36)

    def test_propagates_incoming_x_request_id(self):
        c = Client()
        rid = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'
        r = c.get('/health/', HTTP_X_REQUEST_ID=rid)
        self.assertEqual(r['X-Request-ID'], rid)


class BuildLoggingDictTests(TestCase):
    def test_json_formatter_when_requested(self):
        from config.logging_config import build_logging_dict

        cfg = build_logging_dict(use_json=True)
        self.assertEqual(cfg['handlers']['console']['formatter'], 'json')

    def test_text_formatter_by_default_flag(self):
        from config.logging_config import build_logging_dict

        cfg = build_logging_dict(use_json=False)
        self.assertEqual(cfg['handlers']['console']['formatter'], 'standard')
