from InnotterDjango.aws_metaclass import AWSMeta
from django.conf import settings


class SESClient(metaclass=AWSMeta):
    service_name = 'ses'

    @classmethod
    def send_email_about_new_post(cls, page_name: str, emails: list, posts_url: str) -> None:
        cls.client.send_email(
            Source=settings.AWS_MAIL_SENDER,
            Destination={
                'ToAddresses': emails,
                'BccAddresses': emails
            },
            Message={
                'Subject': {
                    'Data': 'New post!',
                    'Charset': 'UTF-8'
                },
                'Body': {
                    'Html': {
                        'Data': (
                            f'Hello! New post on the page {page_name}!<br>'
                            f'Link to the posts: <b><a href="{posts_url}">'
                            f'Posts on the page {page_name}</a></b>'
                        ),
                        'Charset': 'UTF-8'
                    }
                }
            }
        )

    @classmethod
    def send_email_to_verify_account(cls, email: str, verify_url: str) -> None:
        cls.client.send_email(
            Source=settings.AWS_MAIL_SENDER,
            Destination={
                'ToAddresses': [email],
                'BccAddresses': [email]
            },
            Message={
                'Subject': {
                    'Data': 'Verify account!',
                    'Charset': 'UTF-8'
                },
                'Body': {
                    'Html': {
                        'Data': (
                            f'Click the link below to verify account.<br>'
                            f'<b><a href="{verify_url}">{verify_url}</a></b>'
                        ),
                        'Charset': 'UTF-8'
                    }
                }
            }
        )
