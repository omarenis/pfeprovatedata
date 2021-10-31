import os

from flask import Flask, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, JWTManager
from services import PatientPrivateDataService, UserAuthenticationService
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
JWT = JWTManager(app=app)
USER_SERVICE = UserAuthenticationService()


@app.route('/authenticate', methods=['POST'])
def authenticate():
    account = USER_SERVICE.login(request.json.get('account'), request.json.get('passphrase'))
    if not isinstance(account, Exception):
        return jsonify({
            **account,
            'access': create_access_token(account.get('address'))
        }), 201
    else:
        return jsonify({'message': 'account locked or wrong password'}), 405


@app.route('/signup', methods=['POST'])
def signup():
    account = USER_SERVICE.create_account(request.json.get('passphrase'))
    if isinstance(account, Exception):
        return jsonify({'message': 'server internal error'}), 500
    else:
        return jsonify(account), 201


@app.route('/patients/<int:_id>', methods=['GET', 'POST', 'PUT'])
@jwt_required()
def get_create_patients(_id: int):
    patient_contract = PatientPrivateDataService(contract_address=request.args.get('contractAddress'))
    if request.method == 'POST' or request.method == 'PUT':
        data = request.json
        patient = patient_contract.create_or_update_patient(
            _id=data.get('id'), name=data.get('name'), family_name=data.get('familyName'),
            birthdate=data.get('birthdate'), school=data.get('school'), parent_id=data.get('parentId'),
            passphrase=data.get('account').get('passphrase'), address=data.get('account').get('address'),
            is_new=request.method == 'PUT')
        if isinstance(patient, Exception):
            return jsonify(error=str(patient)), 500
        return jsonify(**patient), 201
    else:
        patient = patient_contract.get_patient_by_id(_id)
        if isinstance(patient, Exception):
            return jsonify(error=str(patient)), 500
        if patient.get('id') == 0:
            return jsonify(error='patient not found'), 404
        return jsonify(patient), 200


if __name__ == '__main__':
    app.run()
