# -*- coding: utf-8 -*-
import re
import datetime
from libcoldstar.plugin_helpers import ColdstarPlugin, Dependency
from twisted.application.service import Service
from twisted.internet.defer import inlineCallbacks


class CronTask(object):
    __slots__ = ['cron', 'task']

    def __init__(self, src):
        self.cron = src['cron']
        self.task = src['task']


class ScheduleManager(Service, ColdstarPlugin):
    """
    I manage scheduled tasks
    """
    signal_name = 'coldstar.schedule_manager'
    db = Dependency('coldstar.db')

    re_cron = re.compile(ur'(.+?)\s+(.+?)\s+(.+?)\s+(.+?)\s+(.+?)')
    re_task = re.compile(ur'((\w+)(\s*\((.*?)\))?)')

    def __init__(self):
        self.schedules = {}
        self.task_functions = {}
        self.started = False
        for key, func in self.__class__.__dict__.iteritems():
            if key.startswith('task_'):
                self.task_functions[key[5:]] = func
        self.config = {
            'schedule': [CronTask({'cron': '0 * * * *', 'task': 'errand_statuses'})]
        }  # вообще надо будет настройки в бд хранить
        self.set_config(self.config)

    def set_config(self, config):
        self.config = config
        from libsch_manager.txscheduling.cron import parseCronEntry, CronSchedule
        from libsch_manager.txscheduling.task import ScheduledCall

        was_started = self.started
        self.stopService()
        self.schedules = {}
        for s in config.get('schedule', []):
            # log.debug(u'Загрузка строки расписания: "%s %s"', s.cron, s.task)
            cron = s.cron
            if cron.startswith('@'):
                cron = cron\
                    .replace('@yearly', '0 0 1 1 *', 1)\
                    .replace('@annually', '0 0 1 1 *', 1)\
                    .replace('@monthly', '0 0 1 * *', 1)\
                    .replace('@weekly', '0 0 * * 0', 1)\
                    .replace('@daily', '0 0 * * *', 1)\
                    .replace('@hourly', '0 * * * *', 1)
            cron_match = self.re_cron.match(cron)
            task_match = self.re_task.match(s.task)
            if not cron_match:
                # log.error(u'Неверный формат строки расписания: "%s"', s.cron)
                continue
            m, h, d, M, w = cron_match.groups()
            full_name, name, _, arg = task_match.groups()
            if not name in self.task_functions:
                # log.warning(u'Задача "%s" не зарегистрирована', name)
                continue

            try:
                schedule = {
                    'minutes': parseCronEntry(m, 0, 59),
                    'hours':   parseCronEntry(h, 0, 23),
                    'doms':    parseCronEntry(d, 1, 31),
                    'months':  parseCronEntry(M, 1, 12),
                    'dows':    parseCronEntry(w, 0, 6),
                }
            except Exception, e:
                # log.error(u'Неверный формат значения в строке расписания\n%s', repr(e))
                continue

            if arg:
                sc = ScheduledCall(self.task_functions[name], self, arg)
            else:
                sc = ScheduledCall(self.task_functions[name], self)

            self.schedules[full_name] = CronSchedule(schedule), sc
        #     log.info(u'Задача "%s" поставлена в очередь', task_match.group(0))
        # log.info(u'Загрузка задач завершена')
        # self.startService()

    def startService(self, now=True):
        # log.debug(u'Запуск службы расписаний')
        for name, (schedule, call) in self.schedules.iteritems():
            if not self.started:
                call.start(schedule, now=now)
        self.started = True

    def stopService(self):
        # log.debug(u'Останов службы расписаний')
        self.started = False
        from twisted.internet.error import AlreadyCancelled, AlreadyCalled
        for name, (schedule, call) in self.schedules.iteritems():
            try:
                call.stop()
            except AlreadyCancelled:
                pass
            except AlreadyCalled:
                pass

    @inlineCallbacks
    def task_errand_statuses(self):
        from coldstar.simargl.client_db_errands import Errand, rbErrandStatus

        with self.db.context_session() as session:
            now = datetime.datetime.now()
            to_update = session.query(Errand).join(rbErrandStatus).filter(Errand.deleted == 0, rbErrandStatus.code == 'waiting').all()
            for errand in to_update:
                if errand.plannedExecDate.date() < now.date() and not errand.execDate:
                    errand.status = session.query(rbErrandStatus).filter(rbErrandStatus.code == 'expired').first()
                    session.add(errand)
            session.commit()