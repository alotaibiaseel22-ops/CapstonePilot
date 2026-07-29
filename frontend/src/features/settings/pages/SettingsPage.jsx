import { useState } from 'react'
import { User as UserIcon, Mail, Lock } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '@/shared/components/ui/card'
import { Input } from '@/shared/components/ui/input'
import { Button } from '@/shared/components/ui/button'
import { useAuth } from '@/app/providers/AuthProvider'
import { useUpdateProfile, useChangePassword } from '../hooks/useSettings'

const roleLabels = {
  project_owner: 'Project Owner',
  collaborator: 'Collaborator',
}

const languageLabels = { en: 'English', ar: 'Arabic' }

function SettingsPage() {
  const { user } = useAuth()
  const updateProfile = useUpdateProfile()
  const changePassword = useChangePassword()

  const [name, setName] = useState('')
  const [language, setLanguage] = useState('')
  const nameValue = name || user?.name || ''
  const languageValue = language || user?.preferred_language || 'en'

  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [passwordError, setPasswordError] = useState(null)

  async function handleSaveProfile(e) {
    e.preventDefault()
    await updateProfile.mutateAsync({ name: nameValue, preferred_language: languageValue })
  }

  async function handleChangePassword(e) {
    e.preventDefault()
    setPasswordError(null)
    if (newPassword !== confirmPassword) {
      setPasswordError("New password and confirmation don't match.")
      return
    }
    await changePassword.mutateAsync({
      current_password: currentPassword,
      new_password: newPassword,
    })
    setCurrentPassword('')
    setNewPassword('')
    setConfirmPassword('')
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="mt-1 text-muted-foreground">Manage your profile and account security.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Profile</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSaveProfile} className="space-y-4">
            <div>
              <label className="mb-2 block text-xs font-semibold tracking-wide text-gray-500">
                NAME
              </label>
              <Input icon={UserIcon} value={nameValue} onChange={(e) => setName(e.target.value)} />
            </div>
            <div>
              <label className="mb-2 block text-xs font-semibold tracking-wide text-gray-500">
                EMAIL
              </label>
              <Input icon={Mail} value={user?.email ?? ''} disabled />
            </div>
            <div>
              <label className="mb-2 block text-xs font-semibold tracking-wide text-gray-500">
                ROLE
              </label>
              <Input value={roleLabels[user?.role] ?? user?.role ?? ''} disabled />
            </div>
            <div>
              <label className="mb-2 block text-xs font-semibold tracking-wide text-gray-500">
                LANGUAGE
              </label>
              <select
                value={languageValue}
                onChange={(e) => setLanguage(e.target.value)}
                className="h-11 w-full rounded-lg border border-border bg-gray-50 px-3 text-sm text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/30"
              >
                {Object.entries(languageLabels).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </div>
            <Button type="submit" size="sm" disabled={updateProfile.isPending}>
              {updateProfile.isPending ? 'Saving...' : 'Save Changes'}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Security</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleChangePassword} className="space-y-4">
            <div>
              <label className="mb-2 block text-xs font-semibold tracking-wide text-gray-500">
                CURRENT PASSWORD
              </label>
              <Input
                icon={Lock}
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                required
              />
            </div>
            <div>
              <label className="mb-2 block text-xs font-semibold tracking-wide text-gray-500">
                NEW PASSWORD
              </label>
              <Input
                icon={Lock}
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                minLength={8}
                required
              />
            </div>
            <div>
              <label className="mb-2 block text-xs font-semibold tracking-wide text-gray-500">
                CONFIRM NEW PASSWORD
              </label>
              <Input
                icon={Lock}
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                minLength={8}
                required
              />
            </div>
            {passwordError && <p className="text-sm text-red-600">{passwordError}</p>}
            <Button type="submit" size="sm" disabled={changePassword.isPending}>
              {changePassword.isPending ? 'Changing...' : 'Change Password'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}

export { SettingsPage }
