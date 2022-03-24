pipeline {
  agent any
  triggers {
    pollSCM('H H * * *')
  }
  stages {
    stage('Build') {
      steps {
        sh 'scons'
      }
    }
  }
  post {
    succcess {
      mail(body: 'kml_tools build successful', subject:'kml_tools build successful', to: 'cjw@ucar.edu janine@ucar.edu cdewerd@ucar.edu taylort@ucar.edu')
    }
  }
  options {
    buildDiscarder(logRotator(numToKeepStr: '10'))
  }
}
