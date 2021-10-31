from services import UserAuthenticationService, PatientPrivateDataService

try:
    contract_address = "0xED8a8da231cBA8dF7DD1c9712F31f99A4c4bda5C"
    patientService = PatientPrivateDataService(contract_address=contract_address)
    userService = UserAuthenticationService()
    account = userService.login("0xa1D692EEEfa1209adA3A9194afd85Af7E72A642E", "11608168")
    print(account)
    if isinstance(account, Exception):
        raise account
    patient = patientService.create_or_update_patient(_id=1, name='ahmed', family_name='triki', birthdate='2017-01-02',
                                                      school='saida', address=account.get('address'),
                                                      passphrase='11608168', is_new=False, parent_id=1)

    print(patient)
    print(patientService.get_patient_by_id(1))
except Exception as exception:
    print(exception)
