pipeline {
  agent {
     node {
        label 'CentOS9_x86_64'
        }
  }
  triggers {
    pollSCM('H/30 6-20 * * *')
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
      emailext to: "cjw@ucar.edu janine@ucar.edu cdewerd@ucar.edu",
      subject: "Jenkinsfile kml_tools build failed",
      body: "See console output attached",
      attachLog: true
    }
  }
  options {
    buildDiscarder(logRotator(numToKeepStr: '10'))
  }
}
