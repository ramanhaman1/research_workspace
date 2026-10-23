
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
                bat '.venv\\Scripts\\python.exe -m pip install --upgrade pip==26.2.2 certifi==2026.10.19'
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
        stage('Dependency Analysis') {
            steps {
                bat '.venv\\Scripts\\python.exe -m pip install pip-audit'
                bat '.venv\\Scripts\\python.exe -m pip_audit --local --format json --output reports\\dependency-audit.json'
            }
        }
    }

    post {
        always {
            junit 'reports/junit.xml'
            archiveArtifacts artifacts: 'reports/*.json, reports/*.xml',
                         allowEmptyArchive: true
        }
    }
}
