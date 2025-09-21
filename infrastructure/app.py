#!/usr/bin/env python3
import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    aws_cognito as cognito,
    aws_s3 as s3,
    Duration,
    RemovalPolicy
)
from constructs import Construct

class LanguageLearningStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # S3 Bucket for media storage
        media_bucket = s3.Bucket(
            self, "MediaBucket",
            bucket_name=f"language-learning-media-{self.account}-{self.region}",
            cors=[s3.CorsRule(
                allowed_methods=[s3.HttpMethods.GET, s3.HttpMethods.POST, s3.HttpMethods.PUT],
                allowed_origins=["*"],
                allowed_headers=["*"]
            )],
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        # DynamoDB Tables
        users_table = dynamodb.Table(
            self, "UsersTable",
            table_name="language-learning-users",
            partition_key=dynamodb.Attribute(name="userId", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY
        )

        lessons_table = dynamodb.Table(
            self, "LessonsTable", 
            table_name="language-learning-lessons",
            partition_key=dynamodb.Attribute(name="lessonId", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY
        )

        vocabulary_table = dynamodb.Table(
            self, "VocabularyTable",
            table_name="language-learning-vocabulary", 
            partition_key=dynamodb.Attribute(name="userId", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="wordId", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY
        )

        # Cognito User Pool
        user_pool = cognito.UserPool(
            self, "UserPool",
            user_pool_name="language-learning-users",
            sign_in_aliases=cognito.SignInAliases(email=True),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True
            ),
            removal_policy=RemovalPolicy.DESTROY
        )

        user_pool_client = cognito.UserPoolClient(
            self, "UserPoolClient",
            user_pool=user_pool,
            generate_secret=False,
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True
            )
        )

        # Lambda execution role with comprehensive permissions
        lambda_role = iam.Role(
            self, "LambdaExecutionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonDynamoDBFullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonTranscribeFullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonPollyFullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonRekognitionFullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonBedrockFullAccess")
            ]
        )

        # Lambda Functions with latest runtime
        user_manager = _lambda.Function(
            self, "UserManager",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="user_manager.handler",
            code=_lambda.Code.from_asset("lambda"),
            role=lambda_role,
            timeout=Duration.seconds(30),
            environment={
                "USERS_TABLE": users_table.table_name
            }
        )

        lesson_generator = _lambda.Function(
            self, "LessonGenerator",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="lesson_generator.handler", 
            code=_lambda.Code.from_asset("lambda"),
            role=lambda_role,
            timeout=Duration.seconds(60),
            environment={
                "USERS_TABLE": users_table.table_name,
                "LESSONS_TABLE": lessons_table.table_name
            }
        )

        quiz_generator = _lambda.Function(
            self, "QuizGenerator",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="quiz_generator.handler",
            code=_lambda.Code.from_asset("lambda"),
            role=lambda_role,
            timeout=Duration.seconds(30)
        )

        vocabulary_manager = _lambda.Function(
            self, "VocabularyManager",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="vocabulary_manager.handler",
            code=_lambda.Code.from_asset("lambda"),
            role=lambda_role,
            timeout=Duration.seconds(15),
            environment={
                "VOCABULARY_TABLE": vocabulary_table.table_name
            }
        )

        voice_processor = _lambda.Function(
            self, "VoiceProcessor",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="voice_processor.handler",
            code=_lambda.Code.from_asset("lambda"),
            role=lambda_role,
            timeout=Duration.seconds(60),
            environment={
                "MEDIA_BUCKET": media_bucket.bucket_name
            }
        )

        voice_transcriber = _lambda.Function(
            self, "VoiceTranscriber",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="voice_transcriber.handler",
            code=_lambda.Code.from_asset("lambda"),
            role=lambda_role,
            timeout=Duration.seconds(60),
            environment={
                "MEDIA_BUCKET": media_bucket.bucket_name
            }
        )

        object_detector = _lambda.Function(
            self, "ObjectDetector",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="object_detector.handler",
            code=_lambda.Code.from_asset("lambda"),
            role=lambda_role,
            timeout=Duration.seconds(30),
            environment={
                "MEDIA_BUCKET": media_bucket.bucket_name
            }
        )

        translator = _lambda.Function(
            self, "Translator",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="translator.handler",
            code=_lambda.Code.from_asset("lambda"),
            role=lambda_role,
            timeout=Duration.seconds(30)
        )

        # API Gateway with CORS
        api = apigw.RestApi(
            self, "LanguageLearningAPI",
            rest_api_name="Language Learning Service",
            description="AI-powered language learning platform",
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "X-Amz-Date", "Authorization", "X-Api-Key"]
            )
        )

        # API Resources and Methods
        users_resource = api.root.add_resource("users")
        users_resource.add_method("GET", apigw.LambdaIntegration(user_manager))
        users_resource.add_method("POST", apigw.LambdaIntegration(user_manager))

        lessons_resource = api.root.add_resource("lessons")
        lessons_resource.add_method("POST", apigw.LambdaIntegration(lesson_generator))

        quiz_resource = api.root.add_resource("quiz")
        quiz_resource.add_method("POST", apigw.LambdaIntegration(quiz_generator))

        vocabulary_resource = api.root.add_resource("vocabulary")
        vocabulary_resource.add_method("GET", apigw.LambdaIntegration(vocabulary_manager))
        vocabulary_resource.add_method("POST", apigw.LambdaIntegration(vocabulary_manager))

        voice_resource = api.root.add_resource("voice")
        voice_resource.add_method("POST", apigw.LambdaIntegration(voice_processor))

        voice_transcribe_resource = api.root.add_resource("voice-transcribe")
        voice_transcribe_resource.add_method("POST", apigw.LambdaIntegration(voice_transcriber))

        objects_resource = api.root.add_resource("objects")
        objects_resource.add_method("POST", apigw.LambdaIntegration(object_detector))

        translate_resource = api.root.add_resource("translate")
        translate_resource.add_method("POST", apigw.LambdaIntegration(translator))

        # Grant permissions
        users_table.grant_read_write_data(user_manager)
        users_table.grant_read_write_data(lesson_generator)
        lessons_table.grant_read_write_data(lesson_generator)
        vocabulary_table.grant_read_write_data(vocabulary_manager)
        
        # Grant S3 permissions
        media_bucket.grant_read_write(voice_processor)
        media_bucket.grant_read_write(voice_transcriber)
        media_bucket.grant_read_write(object_detector)

        # Outputs
        cdk.CfnOutput(self, "APIEndpoint", value=api.url)
        cdk.CfnOutput(self, "UserPoolId", value=user_pool.user_pool_id)
        cdk.CfnOutput(self, "UserPoolClientId", value=user_pool_client.user_pool_client_id)

app = cdk.App()
LanguageLearningStack(app, "LanguageLearningStack")
app.synth()
