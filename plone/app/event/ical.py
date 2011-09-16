import icalendar

from Acquisition import aq_inner
from zope.interface import implementer
from zope.publisher.browser import BrowserView

from plone.app.event.base import default_timezone

# ical adapter implementation interfaces
from plone.app.event.interfaces import IICalendar
from plone.app.event.interfaces import IICalendarComponent

# ical adapter adapting interfaces
from plone.app.collection.interfaces import ICollection
from plone.app.event.interfaces import IEvent

from plone.app.event import messageFactory as _


PRODID = "-//Plone.org//NONSGML plone.event//EN"
VERSION = "2.0"

def construct_calendar(context, events):
    """ Returns an icalendar.Calendar object.

    context: A content object, which is used for calendar details like Title
             and Description. Usually a container, collection or the event
             itself.

    events: The list of event objects, which are included in this calendar.

    """
    cal = icalendar.Calendar()
    cal.add('prodid', PRODID)
    cal.add('version', VERSION)

    # TODO: is there a UUID to use instead of UID?
    # Non-Standard calendar extensions. also see:
    # http://en.wikipedia.org/wiki/ICalendar#cite_note-11
    cal_title = context.Title()
    if cal_title: cal.add('x-wr-calname', cal_title)
    cal_desc = context.Description()
    if cal_desc: cal.add('x-wr-caldesc', cal_desc)
    if getattr(context, 'UID', False): # portal object does not have UID
        cal_uid = context.UID()
        cal.add('x-wr-relcalid', cal_uid)
    cal_tz = default_timezone(context)
    if cal_tz: cal.add('x-wr-timezone', cal_tz)

    for event in events:
        cal.add_component(IICalendarComponent(event))

    return cal


@implementer(IICalendar)
def calendar_component(context):
    """ Container/Event adapter. Returns an icalendar.Calendar object from a
    context like Event, Container or Collection.

    """
    context = aq_inner(context)
    if IEvent.providedBy(context):
        events = [context]
    else:
        query = {'object_provides':IEvent.__identifier__}
        if not ICollection.providedBy(context):
            query['path'] = '/'.join(context.getPhysicalPath())
        events = [item.getObject() for item in context.queryCatalog(REQUEST=query)]

    return construct_calendar(context, events)


class EventsICal(BrowserView):
    """Returns events in iCal format"""

    def __call__(self):
        cal = IICalendar(self.context)
        if not cal: return _(u'ical_view_no_events', default=u'No events found.')

        name = '%s.ics' % self.context.getId()
        self.request.RESPONSE.setHeader('Content-Type', 'text/calendar')
        self.request.RESPONSE.setHeader('Content-Disposition',
            'attachment; filename="%s"' % name)

        # get iCal
        self.request.RESPONSE.write(cal.as_string().encode('utf-8'))
