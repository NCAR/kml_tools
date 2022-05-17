pipeline {
  agent any
  triggers {
    pollSCM('H H * * *')
  }
    stages {
    stage('Build') {
      steps {
        sh 'git submodule update --init --recursive'
        sh 'cd acTrack2kml'
        sh 'scons install'
      }
    }

  }
  post {
    success {
      mail(to: 'cjw@ucar.edu cdewerd@ucar.edu taylort@ucar.edu', subject: 'kml_tools build successful', body: 'kml_tools build successful')
    }
  }
  options {
    buildDiscarder(logRotator(numToKeepStr: '10'))
  }
}
