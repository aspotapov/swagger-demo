import re

from aiohttp import web
from peewee import *
from playhouse.shortcuts import model_to_dict

ROOT_ITEM_ID = 0

db = SqliteDatabase(':memory:')


class Item(Model):
    id = IntegerField(primary_key=True)
    parent = ForeignKeyField('self', null=True)
    header = TextField()
    content = TextField(null=True)
    leaf = BooleanField()

    class Meta:
        database = db


db.create_tables([Item])
Item.create(id=ROOT_ITEM_ID, parent=None, header='Root element', leaf=False)


def check_header(header: str) -> bool:
    if not header:
        return False

    match = re.match(r'^(\w+ )*\w+$', header)
    if not match:
        return False

    return True


def check_header_unique(parent_id: str, header: str, skip_id=None):
    query = Item.select().where(Item.parent == parent_id, Item.header == header)
    if skip_id:
        query = query.where(Item.id != skip_id)

    return not query.exists()


def get_root_item():
    return get_item(ROOT_ITEM_ID)


def get_item(item_id):
    """
    Reads element by ID
    :param item_id: element to read
    :return:
    """

    try:
        item = Item.get_by_id(item_id)
    except DoesNotExist:
        raise web.HTTPBadRequest(body=b"Element doesn't exist")

    reply = model_to_dict(item)

    if not item.leaf:
        query = Item.select().where(Item.parent == item_id)
        reply['children'] = list(query.dicts())

    return web.json_response(reply)


def add_item(body):
    """
    Creates new element with values from 'body'
    :param body: initial values for item
    :return:
    """

    if not check_header(body['header']):
        raise web.HTTPBadRequest(body=b'Element header is invalid')

    if 'parent' not in body or body['parent'] is None:
        body['parent'] = ROOT_ITEM_ID

    try:
        parent = Item.get_by_id(body['parent'])
    except DoesNotExist:
        raise web.HTTPBadRequest(body=b"Element's parent doesn't exist")

    if parent.leaf:
        raise web.HTTPBadRequest(body=b'Parent element is leaf element')

    unique = check_header_unique(body['parent'], body['header'])
    if not unique:
        raise web.HTTPBadRequest(body=b'Element header duplication')

    item = Item.create(parent=body['parent'], header=body['header'], content=body.get('content'), leaf=body['leaf'])

    return web.json_response(model_to_dict(item))


def update_item(item_id, body):
    """
    Updates state if element by ID with values from 'body'
    :param item_id: element to update
    :param body: values to update
    :return:
    """

    if not check_header(body['header']):
        raise web.HTTPBadRequest(body=b'Element header is invalid')

    if item_id == ROOT_ITEM_ID:
        raise web.HTTPBadRequest(body=b"Cannot edit root element")

    if item_id == body['parent']:
        raise web.HTTPBadRequest(body=b"Element cannot be parent of itself")

    try:
        item = Item.get_by_id(item_id)
    except DoesNotExist:
        raise web.HTTPBadRequest(body=b"Element doesn't exist")

    if 'parent' not in body or body['parent'] is None:
        body['parent'] = ROOT_ITEM_ID

    try:
        parent = Item.get_by_id(body['parent'])
    except DoesNotExist:
        raise web.HTTPBadRequest(body=b"Element's parent doesn't doesn't exist")

    if parent.leaf:
        raise web.HTTPBadRequest(body=b'Parent element if leaf element')

    unique = check_header_unique(body['parent'], body['header'], skip_id=item_id)
    if not unique:
        raise web.HTTPBadRequest(body=b'Element header duplication')

    item.parent = body['parent']
    item.header = body['header']
    item.leaf = body['leaf']

    if 'content' in body:
        item.content = body['content']

    item.save()
    return web.json_response(model_to_dict(item))


def delete_item(item_id):
    """
    Deletes element by ID
    :param item_id: element to delete
    :return:
    """

    if item_id == ROOT_ITEM_ID:
        raise web.HTTPBadRequest(body=b"Cannot delete root element")

    try:
        item = Item.get_by_id(item_id)
    except DoesNotExist:
        raise web.HTTPBadRequest(body=b"Element doesn't exist")

    item.delete_instance()
    return web.json_response()
