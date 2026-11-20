pipeline {
    agent any

    environment {
        STUDENT_ID  = 'FA23-BDS-041'
        IMAGE       = 'tehreemtj/midterm-fa23-bds-041'   // Docker Hub repo
        CONTAINER   = 'midterm-app'
        NOTIFY_TO   = 'qasimalik@gmail.com'
        NOTIFY_FROM = 'tjtehreem65@gmail.com'   // <-- the Gmail you put in the Google Form
        MY_EMAIL    = 'tjtehreem65@gmail.com'   // <-- the email my own git commits use (git config user.email)
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
                    env.GIT_SHA         = sh(script: 'git rev-parse HEAD', returnStdout: true).trim()
                    env.COMMITTER_NAME  = sh(script: 'git log -1 --pretty=format:%an', returnStdout: true).trim()
                    env.COMMITTER_EMAIL = sh(script: 'git log -1 --pretty=format:%ae', returnStdout: true).trim()
                }
                sh '''
                    rm -f deployed_metrics.json
                    echo "Commit : $GIT_SHA"
                    echo "Pushed by: $COMMITTER_NAME <$COMMITTER_EMAIL>"
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
        stage('Push to Docker Hub') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub', usernameVariable: 'DH_USER', passwordVariable: 'DH_PASS')]) {
                    sh '''
                        echo "$DH_PASS" | docker login -u "$DH_USER" --password-stdin
                        docker push $IMAGE:$BUILD_NUMBER
                        docker push $IMAGE:latest
                    '''
                }
            }
        }
    }

    post {
        always {
            script {
                def metrics = fileExists('deployed_metrics.json') ? readFile('deployed_metrics.json').trim() : 'n/a (build did not reach deployment)'
                // Email whoever pushed the change.
                // My own pushes -> only me. Anyone else (sir / autograder) -> them + qasimalik@gmail.com.
                def committer = env.COMMITTER_EMAIL ?: ''
                def recipients
                if (committer.toLowerCase() == env.MY_EMAIL.toLowerCase()) {
                    recipients = committer
                } else if (committer) {
                    recipients = committer + ', ' + env.NOTIFY_TO
                } else {
                    recipients = env.NOTIFY_TO
                }
                emailext(
                    to: recipients,
                    from: env.NOTIFY_FROM,
                    replyTo: env.NOTIFY_FROM,
                    subject: "MIDTERM ${env.STUDENT_ID} - Build #${env.BUILD_NUMBER} ${currentBuild.currentResult}",
                    mimeType: 'text/plain',
                    body: """Student Reg No : ${env.STUDENT_ID}
Job            : ${env.JOB_NAME}
Build          : #${env.BUILD_NUMBER}
Result         : ${currentBuild.currentResult}
Git commit     : ${env.GIT_SHA ?: 'n/a'}
Pushed by      : ${env.COMMITTER_NAME ?: 'n/a'} <${env.COMMITTER_EMAIL ?: 'n/a'}>
Build URL      : ${env.BUILD_URL}

Deployed /metrics:
${metrics}
"""
                )
            }
        }
    }
}
