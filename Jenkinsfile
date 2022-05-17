pipeline {
  agent any
  triggers {
    pollSCM('H H * * *')
  }
    stages {
    stage('Build') {
      steps {
        sh 'git submodule update --init --recursive'
        sh 'scons -C acTrack2kml'
      }
    }

  }
  post {
    failure {
      mail(to: 'cjw@ucar.edu cdewerd@ucar.edu taylort@ucar.edu', subject: 'kml_tools build failed', body: 'kml_tools build failed')
    }
  }
  options {
    buildDiscarder(logRotator(numToKeepStr: '10'))
  }
}
