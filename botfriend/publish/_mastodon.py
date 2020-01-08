from nose.tools import set_trace
from mastodon import Mastodon
from botfriend.bot import Publisher

class MastodonPublisher(Publisher):
    def __init__(self, bot, full_config, instance):
        for i in 'client_id', 'access_token':
            if not i in instance:
                raise ValueError(
                    "Mastodon instance missing required configuration item %s: %r" % (
                        i, instance
                    )
                )
        for key in 'api_base_url', 'url':
            url = instance.get(key)
            if url:
                break
        if not url:
            url = "https://mastodon.social"
        self.api = Mastodon(
            client_id = instance['client_id'],
            client_secret = instance['client_secret'],
            access_token = instance['access_token'],
            api_base_url = url
        )
        self.max_chars = instance.get('max_chars', 500)

    def self_test(self):
        # Do something that will raise an exception if the credentials are invalid.
        # Return a string that will let the user know if they somehow gave
        # credentials to the wrong account.
        verification = self.api.account_verify_credentials()
        if 'username' in verification:
            return ['username']
        else:
            # error
            raise Exception(repr(verification))
        
    def publish(self, post, publication):
        media_ids = []
        arguments = dict()
        for attachment in post.attachments:
            if attachment.filename:
                path = self.attachment_path(attachment.filename)
                arguments = dict(media_file=path)
            else:
                arguments = dict(media_file=attachment.content,
                                 mime_type=attachment.media_type)
            if attachment.alt:
                arguments['description'] = attachment.alt
        try:
            media = None
            if arguments:
                media = self.api.media_post(**arguments)
            if media:
                media_ids.append(media['id'])
            content = publication.content or post.content
            content = self.mastodon_safe(content)
            response = self.api.status_post(
                content, media_ids=media_ids, sensitive=post.sensitive
            )
            publication.report_success(response['id'])
        except Exception as e:
            publication.report_failure(e)

    def mastodon_safe(self, content):
        # TODO: What counts as 'safe' depends on the mastodon instance and
        # in the worst case can require arbitrary plugins. But at least in
        # some cases the maximum length might be different.
        if isinstance(content, str):
            content = content.encode("utf8")
        return content[:int(self.max_chars)]


Publisher = MastodonPublisher
