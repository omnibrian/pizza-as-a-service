import json
import logging
import os

import boto3
import jinja2
from botocore.exceptions import ClientError
from chalice import Chalice, Response

STAGE = os.environ.get('STAGE', 'prod')

app = Chalice(app_name='pizza-as-a-service')
app.log.setLevel(logging.INFO)

dynamodb = boto3.client('dynamodb')
pizza_table = f'pizza-{STAGE}'

templateLoader = jinja2.FileSystemLoader(searchpath='./chalicelib/templates')
templateEnv = jinja2.Environment(loader=templateLoader)


def respond_html():
    return 'text/html' in app.current_request.headers.get('accept', '')


@app.route('/', methods=['GET'])
def list_pizza():
    try:
        pizza_list = dynamodb.scan(
            TableName=pizza_table
        )

        if pizza_list.get('Items'):
            item_list = [item['id']['S'] for item in pizza_list['Items']]
            items = [{
                'id': item,
                'url': f'/{item}'
            } for item in item_list]

            list_template = templateEnv.get_template('list.html.j2')

            if respond_html():
                return Response(body=list_template.render(items=items),
                                headers={'Content-Type': 'text/html'})
            else:
                return {
                    'items': items
                }
        else:
            if respond_html():
                return Response(body='Pizza not found.',
                                headers={'Content-Type': 'text/plain'},
                                status_code=404)
            else:
                return Response(body={'error': 'Pizza not found.'},
                                status_code=404)
    except ClientError as e:
        app.log.error(e.response['Error']['Message'])
        return Response(body='Sorry, no slice.',
                        headers={'Content-Type': 'text/plain'},
                        status_code=500)


@app.route('/{pizza}', methods=['GET'])
def get_pizza(pizza):
    try:
        my_pizza = dynamodb.get_item(
            TableName=pizza_table,
            Key={
                'id': {
                    'S': pizza
                }
            }
        )

        detail_template = templateEnv.get_template('detail.html.j2')

        if my_pizza.get('Item') and my_pizza['Item'].get('pizza'):
            if respond_html():
                return Response(
                    body=detail_template.render(
                        id=pizza,
                        item=my_pizza['Item']['pizza']['S']),
                    headers={'Content-Type': 'text/html'})
            else:
                return {
                    'item': my_pizza['Item']['pizza']['S']
                }
        else:
            if respond_html():
                return Response(body=detail_template.render(
                                    id=pizza, item='No pizza are round.'),
                                headers={'Content-Type': 'text/html'},
                                status_code=404)
            else:
                return Response(body={'error': 'No pizza are round.'},
                                status_code=404)
    except ClientError as e:
        app.log.error(e.response['Error']['Message'])
        return Response(body='Dough! Looks like a pizza problem to me.',
                        headers={'Content-Type': 'text/plain'},
                        status_code=500)
