pipeline {
    agent any

    environment {
        STUDENT_ID  = 'FA23-BDS-041'
        IMAGE       = 'midterm-fa23-bds-041'
        CONTAINER   = 'midterm-app'
        NOTIFY_TO   = 'qasimalik@gmail.com'
        NOTIFY_FROM = 'tjtehreem65@gmail.com'   // <-- the Gmail you put in the Google Form
    }

    triggers {
        githubPush()            // run automatically on every GitHub push (webhook)
    }

    options {
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    stages {
        stage('Fetch Latest Data') {
            steps {
                script {
                    env.GIT_SHA = sh(script: 'git rev-parse HEAD', returnStdout: true).trim()
                }
                sh '''
                    rm -f deployed_metrics.json
                    echo "Commit : $GIT_SHA"
                    git log -1 --pretty=format:'Message: %s (%an)%n'
                    echo "Dataset rows (without header): $(( $(wc -l < dataset/train.csv) - 1 ))"
                '''
            }
        }

        stage('Retrain Model (train.py)') {
            steps {
                sh 'docker build --target train --build-arg GIT_COMMIT=$GIT_SHA -t $IMAGE:train .'
                sh 'docker run --rm $IMAGE:train cat artifacts/metrics.json'
            }
        }

        stage('Run Tests') {
            steps {
                sh 'docker build --target test --build-arg GIT_COMMIT=$GIT_SHA -t $IMAGE:test .'
            }
        }

        stage('Build Docker Image') {
            steps {
                sh 'docker build --target runtime --build-arg GIT_COMMIT=$GIT_SHA -t $IMAGE:$BUILD_NUMBER -t $IMAGE:latest .'
            }
        }

        stage('Deploy on EC2') {
            steps {
                sh '''
                    docker rm -f $CONTAINER || true
                    docker run -d --name $CONTAINER --restart unless-stopped -p 8000:8000 $IMAGE:$BUILD_NUMBER
                '''
            }
        }

        stage('Smoke Test') {
            steps {
                sh '''
                    for i in $(seq 1 30); do
                        curl -sf http://localhost:8000/health | grep -q '"ok"' && break
                        sleep 2
                    done
                    curl -sf http://localhost:8000/metrics | tee deployed_metrics.json
                    echo
                    grep -q "$GIT_SHA" deployed_metrics.json
                    curl -sf -X POST http://localhost:8000/predict \
                         -H 'Content-Type: application/json' \
                         -d '{"records":[{"queue_depth":0.5,"staff_gap":0.2,"truck_delay":-0.3,"order_burst":1.1}]}'
                    echo
                    docker image prune -f
                '''
            }
        }
    }

    post {
        always {
            script {
                def metrics = fileExists('deployed_metrics.json') ? readFile('deployed_metrics.json').trim() : 'n/a (build did not reach deployment)'
                emailext(
                    to: env.NOTIFY_TO,
                    from: env.NOTIFY_FROM,
                    replyTo: env.NOTIFY_FROM,
                    subject: "MIDTERM ${env.STUDENT_ID} - Build #${env.BUILD_NUMBER} ${currentBuild.currentResult}",
                    mimeType: 'text/plain',
                    body: """Student Reg No : ${env.STUDENT_ID}
Job            : ${env.JOB_NAME}
Build          : #${env.BUILD_NUMBER}
Result         : ${currentBuild.currentResult}
Git commit     : ${env.GIT_SHA ?: 'n/a'}
Build URL      : ${env.BUILD_URL}

Deployed /metrics:
${metrics}
"""
                )
            }
        }
    }
}
