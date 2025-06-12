import React from 'react';
import { Card, Form, Input, Button, message } from 'antd';
import { useMutation } from '@tanstack/react-query';
import { endpoints } from '../services/api';

interface ChangePasswordForm {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
}

const ChangePassword: React.FC = () => {
  const [form] = Form.useForm();

  const { mutate: changePassword, isPending } = useMutation({
    mutationFn: (data: ChangePasswordForm) => endpoints.changePassword(data),
    onSuccess: () => {
      message.success('Password changed successfully');
      form.resetFields();
    },
    onError: (error) => {
      message.error(error instanceof Error ? error.message : 'Failed to change password');
    },
  });

  const onFinish = (values: ChangePasswordForm) => {
    if (values.newPassword !== values.confirmPassword) {
      message.error('New passwords do not match');
      return;
    }
    changePassword(values);
  };

  return (
    <div>
      <h2 className="mb-4">Change Password</h2>
      <Card style={{ maxWidth: 500 }}>
        <Form
          form={form}
          layout="vertical"
          onFinish={onFinish}
          autoComplete="off"
        >
          <Form.Item
            name="currentPassword"
            label="Current Password"
            rules={[{ required: true, message: 'Please enter your current password' }]}
          >
            <Input.Password />
          </Form.Item>

          <Form.Item
            name="newPassword"
            label="New Password"
            rules={[
              { required: true, message: 'Please enter your new password' },
              { min: 8, message: 'Password must be at least 8 characters' },
              {
                pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]/,
                message: 'Password must contain at least one uppercase letter, one lowercase letter, one number, and one special character',
              },
            ]}
          >
            <Input.Password />
          </Form.Item>

          <Form.Item
            name="confirmPassword"
            label="Confirm New Password"
            rules={[
              { required: true, message: 'Please confirm your new password' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('newPassword') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('The two passwords do not match'));
                },
              }),
            ]}
          >
            <Input.Password />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" loading={isPending} block>
              Change Password
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
};

export default ChangePassword; 