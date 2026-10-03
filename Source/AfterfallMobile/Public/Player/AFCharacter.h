#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "AFCharacter.generated.h"

class UCameraComponent;
class USpringArmComponent;
class UAFHealthComponent;

UCLASS()
class AFTERFALLMOBILE_API AAFCharacter : public ACharacter
{
    GENERATED_BODY()

public:
    AAFCharacter();

    virtual void SetupPlayerInputComponent(class UInputComponent* PlayerInputComponent) override;

    UFUNCTION(BlueprintCallable, Category="Afterfall|Combat")
    void FirePrimary();

    UFUNCTION(BlueprintCallable, Category="Afterfall|Movement")
    void MoveForward(float Value);

    UFUNCTION(BlueprintCallable, Category="Afterfall|Movement")
    void MoveRight(float Value);

    UFUNCTION(BlueprintCallable, Category="Afterfall|Camera")
    void LookYaw(float Value);

    UFUNCTION(BlueprintCallable, Category="Afterfall|Camera")
    void LookPitch(float Value);

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Afterfall|Camera")
    TObjectPtr<USpringArmComponent> CameraBoom;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Afterfall|Camera")
    TObjectPtr<UCameraComponent> FollowCamera;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Afterfall|Health")
    TObjectPtr<UAFHealthComponent> HealthComponent;

protected:
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Combat", meta=(ClampMin="1.0"))
    float PrimaryDamage = 25.0f;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category="Afterfall|Combat", meta=(ClampMin="100.0"))
    float FireRange = 12000.0f;
};
