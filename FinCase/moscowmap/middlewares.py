# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

import re
import random
import base64
import logging
import requests
from scrapy import signals

log = logging.getLogger('scrapy.proxies')

class Mode:
  RANDOMIZE_PROXY_EVERY_REQUESTS, RANDOMIZE_PROXY_ONCE, SET_CUSTOM_PROXY = range(3)

class RandomProxy(object):
  def __init__(self, settings):
    proxy_settings = settings.get('PROXY_SETTINGS', dict())
    self.chosen_proxy = ''

    self.mode = proxy_settings.get('mode',0)
    self.proxy_list = proxy_settings.get('list',list())
    self.use_real_ip = proxy_settings.get('use_real_when_empty',False)
    self.from_proxies_server = proxy_settings.get('from_proxies_server',False)
    self.custom_proxy = proxy_settings.get('custom_proxy','')


    if (self.mode == Mode.RANDOMIZE_PROXY_EVERY_REQUESTS
        or self.mode == Mode.RANDOMIZE_PROXY_ONCE):
      if not (self.proxy_list or isinstance(self.proxy_list, list)):
        raise KeyError('PROXY_LIST setting is missing')

    elif self.mode == Mode.SET_CUSTOM_PROXY and self.custom_proxy:
      self.proxy_list = list(self.custom_proxy)
    else:
      raise KeyError('unknown Mode, RANDOMIZE_PROXY_EVERY_REQUESTS, RANDOMIZE_PROXY_ONCE, SET_CUSTOM_PROXY plz!')

    if not self.proxy_list:
      if self.use_real_ip:
        return
      else:
        raise KeyError('PROXIES is empty')

    self.proxies = {}
    try:
      for line in self.proxy_list:
        parts = re.match('(\\w+://)([^:]+?:[^@]+?@)?(.+)', line.strip())
        if not parts:
          continue

        # Cut trailing @
        if parts.group(2):
          user_pass = parts.group(2)[:-1]
        else:
          user_pass = ''

        self.proxies[parts.group(1) + parts.group(3)] = user_pass
    except Exception as e:
      logging.exception(e)

    if (self.mode == Mode.RANDOMIZE_PROXY_ONCE
        or self.mode == Mode.SET_CUSTOM_PROXY):
      self.chosen_proxy = random.choice(list(self.proxies.keys()))

  @classmethod
  def from_crawler(cls, crawler):
    return cls(crawler.settings)

  def process_request(self, request, spider):
    # Don't overwrite with a random one (server-side state for IP)
    if 'proxy' in request.meta:
      if request.meta["exception"] is False:
        return
    request.meta["exception"] = False
    if len(self.proxies) == 0:
      if self.use_real_ip:
        return
      else:
        raise ValueError('All proxies are unusable, cannot proceed')

    if self.mode == Mode.RANDOMIZE_PROXY_EVERY_REQUESTS:
      proxy_address = random.choice(list(self.proxies.keys()))
    else:
      proxy_address = self.chosen_proxy

    proxy_user_pass = self.proxies[proxy_address]

    if proxy_address:
      request.meta['proxy'] = proxy_address

    if proxy_user_pass:
      basic_auth = 'Basic ' + base64.b64encode(proxy_user_pass.encode()).decode()
      request.headers['Proxy-Authorization'] = basic_auth

    log.debug('Using proxy <%s>, %d proxies left' % (proxy_address, len(self.proxies)))

  def process_exception(self, request, exception, spider):
    if 'proxy' not in request.meta:
      return
    if (self.mode == Mode.RANDOMIZE_PROXY_EVERY_REQUESTS
        or self.mode == Mode.RANDOMIZE_PROXY_ONCE):
      proxy = request.meta['proxy']
      try:
        del self.proxies[proxy]
      except KeyError:
        pass
      request.meta["exception"] = True
      if self.mode == Mode.RANDOMIZE_PROXY_ONCE:
        self.chosen_proxy = random.choice(list(self.proxies.keys()))
      log.info('Removing failed proxy <%s>, %d proxies left' % (proxy, len(self.proxies)))
