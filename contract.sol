pragma solidity ^0.8;
contract PrivateData{
    uint256 numberPatients = 0;
    struct Patient{
        uint256 id;
        string name;
        string familyName;
        string birthdate;
        string school;
        uint256 parentId;
    }
    mapping(uint256 => Patient) public patients;
    uint256[] public patientsIds;


    function  createPatient(uint256 id, string memory name, string memory familyName, string memory birthdate,
        string memory school, uint256 parentId) public{
        patients[id] = Patient(id, name, familyName, birthdate, school, parentId);
        patientsIds.push(id);
    }

    function getPatientById(uint256 id) public view returns(Patient memory){
        return patients[id];
    }

    function deletePatient(uint256 id) public returns (bool){
        delete patients[id];
        for(uint256 i = 0; i < numberPatients; i++){
            if(patientsIds[i] == id){
                patientsIds[i] = patientsIds[patientsIds.length -1];
                delete patientsIds[patientsIds.length - 1];
                return true;
            }
        }
        return false;
    }


    function updatePatient(uint256 id, string memory name, string memory familyName, string memory birthdate,
        string memory school) public{
        Patient memory patient = patients[id];
        patient.name = name;
        patient.familyName = familyName;
        patient.birthdate = birthdate;
        patient.school = school;
        patients[id] = patient;
    }

    function filterPatient(string memory name, string memory familyName, string memory school, string memory birthdate, uint256 parentId) public view returns (Patient memory){
        for(uint i = 0; i < patientsIds.length; i++){
            if(keccak256(bytes(patients[patientsIds[i]].name)) == keccak256(bytes(name)) && keccak256(bytes(patients[patientsIds[i]].familyName)) == keccak256(bytes(familyName))
            && keccak256(bytes(patients[patientsIds[i]].birthdate)) == keccak256(bytes(birthdate)) && keccak256(bytes(patients[patientsIds[i]].school)) == keccak256(bytes(school)) &&
            patients[patientsIds[i]].parentId == parentId){
                return patients[patientsIds[i]];
            }
        }
        return Patient(0, '', '', '', '', 0);
    }
}
