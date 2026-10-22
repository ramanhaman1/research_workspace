
pipeline {
    agent { label 'windows-python312' }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup') {
            steps {
                bat 'py -3.12 -m venv .venv'
                bat '.venv\\Scripts\\python.exe -m pip install -r requirements.txt'
                bat '.venv\\Scripts\\python.exe -m pip install -e packages\\csv_helper'
            }
        }

        stage('Tests') {
            steps {
                bat '.venv\\Scripts\\python.exe -m pytest tests -q --junitxml=reports\\junit.xml'
            }
        }

        stage('Security Scan') {
            steps {
                bat '.venv\\Scripts\\python.exe -m bandit -r services packages -q'
            }
        }
    }

    post {
        always {
            junit allowEmptyResults: true, testResults: 'reports/junit.xml'
        }
    }
}
